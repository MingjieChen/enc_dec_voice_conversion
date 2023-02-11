#!/bin/bash


# model setup
ling_enc=vqw2v
spk_enc=uttdvec
pros_enc=none
dec=tacoar
vocoder=libritts_hifigan

# exp setup
exp_name=first_train
exp_dir=exp/${ling_enc}_${spk_enc}_${pros_enc}_${dec}/${exp_name}

# eval setup
task=oneshot_vc
epochs=$( ls -t $exp_dir/ckpt | head -n 1 | sed 's/[^0-9]*//g')
eval_list=data/libritts/eval_clean/eval_list_oneshot_vc_small.json
# sge submitjob setup
n_parallel_jobs=50
device=cpu
job=$exp_dir/scripts/inference_${task}_${epochs}.sh
log=$exp_dir/logs/inference_${task}_${epochs}.log
touch $job
chmod +x $job

# create bash file
cat <<EOF > $job

#!/bin/bash
conda=/share/mini1/sw/std/python/anaconda3-2019.07/v3.7
conda_env=torch_1.9
source \$conda/bin/activate \$conda_env
echo "sge_task_id \$SGE_TASK_ID"
python inference.py \
        --exp_dir $exp_dir \
        --eval_list $eval_list \
        --epochs ${epochs} \
        --task ${task} \
        --vocoder ${vocoder}  \
        --device ${device} \
        --sge_task_id \$SGE_TASK_ID \
        --sge_n_tasks ${n_parallel_jobs}

EOF

#submit to sge
submitjob -m 20000 -n $n_parallel_jobs   $log $job
echo "job submitted, see log in ${log}"