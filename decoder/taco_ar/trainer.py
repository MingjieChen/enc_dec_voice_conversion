
import os
import os.path as osp
import sys
import time
from collections import defaultdict

import numpy as np
import torch
from torch import nn
from tqdm import tqdm
from munch import Munch
import torch.nn.functional as F
from .loss import compute_loss, Loss
from .optimizer import build_optimizer


class Trainer(object):
    def __init__(self,
                 args = None,
                 model=None,
                 model_ema=None,
                 optimizer=None,
                 scheduler=None,
                 config={},
                 device=torch.device("cpu"),
                 train_dataloader=None,
                 dev_dataloader=None,
                 initial_steps=0,
                 initial_epochs=0,
                 fp16_run=False,
                 step_writer = None
    ):
        
        self.args = args
        self.steps = initial_steps
        self.epochs = initial_epochs
        self.model = model
        self.model_ema = model_ema
        self.train_dataloader = train_dataloader
        self.dev_dataloader = dev_dataloader
        self.config = config
        self.device = device
        self.finish_train = False
        self.fp16_run = fp16_run
        self.step_writer = step_writer
        print(f'trainer device {self.device}')
        self.iters = 0

        self.objective = Loss()
        self.optimizer, self.scheduler = build_optimizer(model, config)

    def save_checkpoint(self, checkpoint_path):
        """Save checkpoint.
        Args:
            checkpoint_path (str): Checkpoint path to be saved.
        """
        state_dict = {
            "optimizer": self.optimizer.state_dict(),
            'scheduler': self.scheduler.state_dict(),
            "steps": self.steps,
            "epochs": self.epochs,
            "model": self.model.state_dict(),
            "iters": self.iters
        }
        if self.model_ema is not None:
            state_dict['model_ema'] = self.model_ema.state_dict()

        if not os.path.exists(os.path.dirname(checkpoint_path)):
            os.makedirs(os.path.dirname(checkpoint_path))
        torch.save(state_dict, checkpoint_path)

    def load_checkpoint(self, checkpoint_path, load_only_params=False):
        """Load checkpoint.

        Args:
            checkpoint_path (str): Checkpoint path to be loaded.
            load_only_params (bool): Whether to load only model parameters.

        """
        state_dict = torch.load(checkpoint_path, map_location="cpu")
        self._load(state_dict["model"], self.model)

        if self.model_ema is not None:
            self._load(state_dict["model_ema"], self.model_ema)
        
        if not load_only_params:
            self.steps = state_dict["steps"]
            self.epochs = state_dict["epochs"]
            self.iters = state_dict['iters']
            self.optimizer.load_state_dict(state_dict["optimizer"])
            self.scheduler.load_state_dict(state_dict['scheduler'])


    def _load(self, states, model, force_load=True):
        model_states = model.state_dict()
        for key, val in states.items():
            try:
                if key not in model_states:
                    continue
                if isinstance(val, nn.Parameter):
                    val = val.data

                if val.shape != model_states[key].shape:
                    self.logger.info("%s does not have same shape" % key)
                    print(val.shape, model_states[key].shape)
                    if not force_load:
                        continue

                    min_shape = np.minimum(np.array(val.shape), np.array(model_states[key].shape))
                    slices = [slice(0, min_index) for min_index in min_shape]
                    model_states[key][slices].copy_(val[slices])
                else:
                    model_states[key].copy_(val)
            except:
                print("not exist ", key)

    @staticmethod
    def get_gradient_norm(model):
        total_norm = 0
        for p in model.parameters():
            param_norm = p.grad.data.norm(2)
            total_norm += param_norm.item() ** 2

        total_norm = np.sqrt(total_norm)
        return total_norm
    def _get_lr(self):
        for param_group in self.optimizer.param_groups:
            lr = param_group['lr']
            break
        return lr

    @staticmethod
    def moving_average(model, model_test, beta=0.999):
        for param, param_test in zip(model.parameters(), model_test.parameters()):
            param_test.data = torch.lerp(param.data, param_test.data, beta)
    
    
    def _train_epoch(self):
        self.epochs += 1
        
        train_losses = defaultdict(list)
        self.model.train() 
        #scaler = torch.cuda.amp.GradScaler() if (('cuda' in str(self.device)) and self.fp16_run) else None

        
        for train_steps_per_epoch, batch in tqdm(enumerate(self.train_dataloader, 1)):
            #batch = [b.to(self.device) for b in batch ]
            _batch = []
            shapes = ""
            for b in batch:
                if isinstance(b, torch.Tensor):
                    _batch.append(b.to(self.device))
                    #shapes += f' {b.size()}  '
                else:
                    _batch.append(b)    
            
            #print(f'shapes {shapes}', flush = True)        
            
            self.optimizer.zero_grad()
            loss, losses = compute_loss(self.model, _batch, self.objective)        
            loss.backward()
            self.optimizer.step()
            loss_string = f" epoch {self.epochs}, iters {self.iters}" 
            for key in losses:
                train_losses["train/%s" % key].append(losses[key])
                loss_string += f" {key}:{losses[key]:.5f} "
                self.step_writer.add_scalar('step/'+key, losses[key], self.iters)
            self.step_writer.add_scalar('step/lr', self._get_lr(), self.iters)    
            #print(loss_string, flush = True)    
            self.iters+=1
            self.scheduler.step()
                
            if (self.iters % self.config['save_freq']) == 0:
                exp_dir = osp.join(self.config['log_dir'],self.config['model_name'],self.config['exp_name'])
                self.save_checkpoint(osp.join(exp_dir, f'epoch_{self.iters}.pth'))
        train_losses = {key: np.mean(value) for key, value in train_losses.items()}
        return train_losses
    
    
    @torch.no_grad()
    def _eval_epoch(self):
        
        eval_losses = defaultdict(list)
        self.model
        for eval_steps_per_epoch, batchs in enumerate(self.dev_dataloader, 1):
            _batch = []
            for b in batch:
                if isinstance(b, torch.Tensor):
                    _batch.append(b.to(self.device))
                else:
                    _batch.append(b)    
            loss, losses = compute_loss(self.model, _batch, self.objective)        
            for key in losses:
                eval_losses["eval/%s" % key].append(losses[key])
        
        eval_losses = {key: np.mean(value) for key, value in eval_losses.items()}
        eval_string = f"epoch {self.epochs}, eval: "
        for key, value in eval_losses.items():
            eval_string += f"{key}: {value:.6f} "
        #print(eval_string, flush = True)    
        #print()
        return eval_losses
