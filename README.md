# enc_dec_voice_conversion
Work in progress.

A voice conversion framework for different types of encoder and decoders. The encoder-decoder framework is demonstrated in the following ![enc_dec_voice_conversion.drawio.png](figure)

This repo covers all the pipelines from dataset downloading to evaluation.

# Working progress

1. Linguistic Encoder
 - [x] conformer_ppg from [ppg-vc](https://github.com/liusongxiang/ppg-vc)
 - [x] vq-wav2vec from [fairseq](https://github.com/facebookresearch/fairseq)
 - [x] hubert_soft and hubert_discrete from [soft-vc](https://github.com/bshall/soft-vc)
2. Prosodic Encoder
 - [x] log-f0 from [ppg-vc](https://github.com/liusongxiang/ppg-vc)
 - [x] pitch + energy from [fastspeech2](https://github.com/ming024/FastSpeech2)
3. Speaker Encoder
 - [x] d-vector from [ppg-vc](https://github.com/liusongxiang/ppg-vc)
4. Decoder
 - [x] fastspeech2 from [fastspeech2](https://github.com/ming024/FastSpeech2)
 - [x] taco_ar from [s3prl-vc](https://github.com/s3prl/s3prl/tree/main/s3prl/downstream/a2a-vc-vctk)
 - [x] taco_mol from [ppg-vc](https://github.com/liusongxiang/ppg-vc)
 - [x] vits from [vits](https://github.com/jaywalnut310/vits)
5. Vocoder
 - [x] vctk_hifigan from [ppg-vc](https://github.com/liusongxiang/ppg-vc)

# How to run

more to come ...
