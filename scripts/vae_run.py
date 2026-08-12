import os
import sys

# vae_main.py lives next to this file, but the pipeline is invoked from the repo
# root (so that data/ and results/ paths resolve), hence the explicit path.
HERE = os.path.dirname(os.path.abspath(__file__))
VAE_MAIN = os.path.join(HERE, 'vae_main.py')

#os.system('CUDA_VISIBLE_DEVICES="0" python3 vae_main.py -mt vae -ol mRNA@ -hn 4096 -lr 0.001 -dr 0 -wd 1e-5 -dv cuda -cd 0 -sn vae_pretrained -fc None -mx 500 -af Tanh -mo Adam -bs 0 -vd ember_libfm_200115 -sm')
os.system(f'{sys.executable} {VAE_MAIN} -mt vae -ol mRNA@ -hn 4096 -lr 0.001 -dr 0 -wd 1e-5 -dv cpu -cd 0 -sn vae_pretrained -fc None -mx 50 -af Tanh -mo Adam -bs 0 -vd toyforVAE -sm')
