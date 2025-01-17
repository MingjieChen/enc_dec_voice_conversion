from .ppgvc_hifigan.hifigan_model import load_hifigan_generator
from .libritts_hifigan.vocoder import libritts_hifigan_model
from .vctk_hifigan.vocoder import vctk_hifigan_model
from .bigvgan.models import BigVGAN
from sklearn.preprocessing import StandardScaler
import numpy as np
import torch
import json

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

def load_bigvgan(ckpt = '/share/mini1/res/t/vc/studio/timap-en/svcc2023/BigVGAN/exp/bigvgan/g_00776000', config = '/share/mini1/res/t/vc/studio/timap-en/svcc2023/BigVGAN/exp/bigvgan/config.json', device = 'cpu'):
    with open(config) as f:
        model_config = f.read()
    h = json.loads(model_config)
    h = AttrDict(h)    
    model = BigVGAN(h).to(device)
    state_dict_g = torch.load(ckpt, map_location=device)
    model.load_state_dict(state_dict_g['generator'])
    model.eval()
    model.remove_weight_norm()
    return model
    
def load_ppgvc_hifigan(ckpt = None, config = None, device = 'cpu'):
    model = load_hifigan_generator(device)
    return model

def load_libritts_hifigan(ckpt = 'vocoder/libritts_hifigan/model.pkl', config = 'vocoder/libritts_hifigan/config.yml', stats = 'vocoder/libritts_hifigan/stats.npy', device = 'cpu'):
    scaler = StandardScaler()
    scaler.mean_ = np.load(stats)[0]
    scaler.scale_ = np.load(stats)[1]
    scaler.n_features_in = scaler.mean_.shape[0]
    

    model = libritts_hifigan_model(ckpt, config, device)
    return (model, scaler)


def bigvgan(model, mel):
    MAX_WAV_VALUE = 32768.0
    audio = model(mel.transpose(1,2)).view(-1)

    #audio = y_g_hat.squeeze()
    #audio = audio * MAX_WAV_VALUE
    #audio = audio.cpu().numpy().astype('int16')
    return audio
def libritts_hifigan(model, mel):
    
    hifigan_model, scaler = model
    mean_tensor = torch.FloatTensor(scaler.mean_).to(mel.device)
    std_tensor = torch.FloatTensor(scaler.scale_).to(mel.device)
    mel = (mel - mean_tensor) / (std_tensor + 1e-8)
    wav = hifigan_model.inference(mel.squeeze(0)).view(-1)        

    return wav

def load_vctk_hifigan(ckpt = 'vocoder/vctk_hifigan/model.pkl', config = 'vocoder/vctk_hifigan/config.yml', stats = 'vocoder/vctk_hifigan/stats.npy', device = 'cpu'):
    
    scaler = StandardScaler()
    scaler.mean_ = np.load(stats)[0]
    scaler.scale_ = np.load(stats)[1]
    scaler.n_features_in = scaler.mean_.shape[0]
    model = vctk_hifigan_model(ckpt, config, device)
    return (model, scaler)

def vctk_hifigan(model, mel ):
    

    hifigan_model, scaler = model
    mean_tensor = torch.FloatTensor(scaler.mean_).to(mel.device)
    std_tensor = torch.FloatTensor(scaler.scale_).to(mel.device)
    mel = (mel - mean_tensor) / (std_tensor + 1e-8)
    wav = hifigan_model.inference(mel.squeeze(0)).view(-1)        

    return wav
def ppgvc_hifigan(model, mel):
    
    wav = model(mel.transpose(1,2)).view(-1)
    return wav     
