# -*- coding: utf-8 -*-
"""image_style_transfer.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1CKL83AgNmQuDveoF37un25YeMOAWBEPV
"""

from __future__ import division
from torch.backends import cudnn
from torch.autograd import Variable
from torchvision import models
from torchvision import transforms
from PIL import Image
import argparse
import torch
import torchvision
import torch.nn as nn
import numpy as np

use_cuda=torch.cuda.is_available()
dtype=torch.cuda.FloatTensor if use_cuda else torch.FloatTensor

def load_image(image_path,transform=None,max_size=None,shape=None):
  image=Image.open(image_path)
  
  if max_size is not None:
    scale=max_size / max(image.size)
    size=np.array(image.size)*scale
    image=image.resize(size.astype(int),Image.ANTIALIAS)
  
  if shape is not None:
    image=image.resize(shape,Image.LANCZOS)
  
  if transform is not None:
    image=transform(image).unsqueeze(0)
  
  return image.type(dtype)

class VGGNet(nn.Module):
  def __init__(self):
    super(VGGNet,self).__init__()
    self.select=['0','5','10','19','28']
    self.vgg=models.vgg19(pretrained=True).features
  
  def forward(self,x):
    features=[]
    for name,layer in self.vgg._modules.items():
      x=layer(x)
      if name in self.select:
        features.append(x)
    return features

def main(config):
  transform=transforms.Compose([
      transforms.ToTensor(),
      transforms.Normalize((0.485,0.456,0.406),
                           (0.229,0.224,0.225))
  ])
  
  content=load_image(config['content'],transform,max_size=config['max_size'])
  style=load_image(config['style'],transform,shape=[content.size(2),content.size(3)])
  
  target=Variable(content.clone(),requires_grad=True)
  optimizer=torch.optim.Adam([target],lr=config['lr'],betas=[0.5,0.999])
  
  vgg=VGGNet()
  if use_cuda:
    vgg.cuda()
  
  for step in range(config['total_step']):
    target_features=vgg(target)
    content_features=vgg(Variable(content))
    style_features=vgg(Variable(style))
    
    style_loss=0
    content_loss=0
    
    for f1,f2,f3 in zip(target_features,content_features,style_features):
      content_loss += torch.mean((f1-f2)**2)
      
      _,c,h,w=f1.size()
      f1=f1.view(c,h*w)
      f3=f3.view(c,h*w)
      
      f1=torch.mm(f1,f1.t())
      f3=torch.mm(f3,f3.t())
      
      style_loss += torch.mean((f1-f3)**2)/(c*h*w)
    
    loss = content_loss + config['style_weight'] * style_loss
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    
    if(step+1)%config['log_step']==0:
      print ('Step [%d/%d], Content Loss: %.4f, Style Loss: %.4f'%(step+1, config['total_step'], content_loss.data[0], style_loss.data[0]))
    
    if(step+1)%config['sample_step']==0:
      denorm=transforms.Normalize((-2.12,-2.04,-1.80),
                                  (4.37,4.46,4.44))
      img=target.clone().cpu().squeeze()
      img=denorm(img.data).clamp_(0,1)
      torchvision.utils.save_image(img,"output-%d.png"%(step+1))

config = {'content':'./dancing.png',
         'style':'./picasso.png',
         'max_size':400,
         'total_step':5000,
         'log_step':10,
         'sample_step':1000,
         'style_weight':100,
         'lr':0.003}

print(config)

main(config)

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
plt.figure()
img=mpimg.imread('dancing.png',0)
imgplot = plt.imshow(img)
plt.show()

plt.figure()
img=mpimg.imread('output-5000.png')
imgplot = plt.imshow(img)
plt.show()

