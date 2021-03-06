import torch
import torch.nn as nn
from torch.nn.modules import padding
from torchsummary import summary


#####################################################################################################################################################
######                                                  InceptionNet_v1                                                                         #####
#####################################################################################################################################################

class InceptionNet_v1(nn.Module):
    def __init__(self,in_channels=1):
        super(InceptionNet_v1,self).__init__()
        self.conv1 = conv_block(in_channels=in_channels,out_channels=64,kernel_size=(5,5,5),stride=(1,1,1),padding=(2,2,2))
        self.maxpool = nn.MaxPool3d(kernel_size=2,stride=2)
        self.conv2 = conv_block(in_channels=64,out_channels=64,kernel_size=(5,5,5),stride=(1,1,1),padding=(2,2,2))
        self.maxpool = nn.MaxPool3d(kernel_size=2,stride=2)
        self.conv3 = conv_block(in_channels=64,out_channels=192,kernel_size=(3,3,3),stride=(1,1,1),padding=(1,1,1))
        
        #Inception block
        self.inception3 = Inception_Block(in_channels=192,out_1x1x1=64,red_3x3x3=96,out_3x3x3=128,red_5x5x5=16,out_5x5x5=32,out_1x1x1_pool=32)
        self.inception4 = Inception_Block(in_channels=256,out_1x1x1=192,red_3x3x3=96,out_3x3x3=208,red_5x5x5=16,out_5x5x5=48,out_1x1x1_pool=64)
        self.inception5 = Inception_Block(in_channels=512,out_1x1x1=384,red_3x3x3=192,out_3x3x3=384,red_5x5x5=48,out_5x5x5=128,out_1x1x1_pool=128)
        self.inception6 = Inception_Block(in_channels=1024,out_1x1x1=384,red_3x3x3=192,out_3x3x3=384,red_5x5x5=48,out_5x5x5=128,out_1x1x1_pool=128)
        
        self.avgpool = nn.AvgPool3d(kernel_size=2,stride=1)

        self.dropout = nn.Dropout3d(p=0.4)

        self.fc1 = nn.Linear(1024,512)
        self.fc2 = nn.Linear(512,64)
        self.fc3 = nn.Linear(64,1)
        self.sigmoid = nn.Sigmoid()

        self.relu = nn.ReLU()

    def forward(self,x):
       x = self.conv1(x)
       x = self.maxpool(x)
       x = self.conv2(x)
       x = self.maxpool(x)
       x = self.conv3(x)
       x = self.maxpool(x)
       
       
       x = self.inception3(x)
       x = self.maxpool(x)
       x = self.inception4(x)
       x = self.maxpool(x)
       x = self.inception5(x)
       x = self.maxpool(x)
       x = self.inception6(x)
       x = self.avgpool(x)
       
       x = x.view(x.size(0),-1)
       x = self.dropout(x)

       x = self.fc1(x)
       x = self.relu(self.fc2(x))
       x = self.sigmoid(self.fc3(x))

       return x


class Inception_Block(nn.Module):
    def __init__(self,in_channels,out_1x1x1,red_3x3x3,out_3x3x3,red_5x5x5,out_5x5x5,out_1x1x1_pool):
        super(Inception_Block,self).__init__()

        self.branch_1 = conv_block(in_channels,out_1x1x1,kernel_size=1)
        self.branch_2 = nn.Sequential(conv_block(in_channels,red_3x3x3,kernel_size=1),conv_block(red_3x3x3,out_3x3x3,kernel_size=3,stride=1,padding=1))
        self.branch_3 = nn.Sequential(conv_block(in_channels,red_5x5x5,kernel_size=1),conv_block(red_5x5x5,out_5x5x5,kernel_size=5,stride=1,padding=2))
        self.branch_4 = nn.Sequential(nn.MaxPool3d(kernel_size=3,stride=1,padding=1),conv_block(in_channels,out_1x1x1_pool,kernel_size=1))

    def forward(self,x):
        return torch.cat([self.branch_1(x),self.branch_2(x),self.branch_3(x),self.branch_4(x)],1)


#############################################################################################################################################################
#####                                                           InceptionNet_v3                                                                         #####
#############################################################################################################################################################
class InceptionNet_v3(nn.Module):
    def __init__(self,in_channels=1):
        super(InceptionNet_v3,self).__init__()
        self.conv1 = conv_block(in_channels=in_channels,out_channels=64,kernel_size=(5,5,5),stride=(1,1,1),padding=(2,2,2))
        self.maxpool = nn.MaxPool3d(kernel_size=2,stride=2)
        self.conv2 = conv_block(in_channels=64,out_channels=192,kernel_size=(3,3,3),stride=(1,1,1),padding=(1,1,1))
        
        #Inception block
        self.inception3 = Inception_Block_v3(in_channels=192,out_1x1x1=32,red1_3x3x3=64, red2_3x3x3=64, out_3x3x3=128, red_3x3x3=64, out2_3x3x3=64, out_1x1x1_pool=32)
        self.inception4 = Inception_Block_v3(in_channels=256,out_1x1x1=128,red1_3x3x3=128, red2_3x3x3=128, out_3x3x3=128, red_3x3x3=64, out2_3x3x3=128, out_1x1x1_pool=128)
        self.inception5 = Inception_Block_v3(in_channels=512,out_1x1x1=128,red1_3x3x3=256, red2_3x3x3=256, out_3x3x3=384, red_3x3x3=256, out2_3x3x3=384, out_1x1x1_pool=128)
        self.inception6 = Inception_Block_v3(in_channels=1024,out_1x1x1=128,red1_3x3x3=256, red2_3x3x3=256, out_3x3x3=384, red_3x3x3=256, out2_3x3x3=384, out_1x1x1_pool=128)
        
        self.avgpool = nn.AvgPool3d(kernel_size=4,stride=1)
        
        self.dropout = nn.Dropout3d(p=0.4)

        self.fc1 = nn.Linear(1024,512)
        self.fc2 = nn.Linear(512,64)
        self.fc3 = nn.Linear(64,1)
        self.sigmoid = nn.Sigmoid()

        self.relu = nn.ReLU()

    def forward(self,x):
       x = self.conv1(x)
       x = self.maxpool(x)
       
       x = self.conv2(x)
       x = self.maxpool(x)
       
       x = self.inception3(x)
       x = self.maxpool(x)
       x = self.inception4(x)
       x = self.maxpool(x)
       x = self.inception5(x)
       x = self.maxpool(x)
       x = self.inception6(x)
       x = self.avgpool(x)
       # print(x.shape)
       x = x.view(x.size(0),-1)
       
       x = self.dropout(x)
        
       x = self.fc1(x)
       x = self.relu(self.fc2(x))
       x = self.sigmoid(self.fc3(x))

       return x


class Inception_Block_v3(nn.Module):
    def __init__(self,in_channels,out_1x1x1,red1_3x3x3,red2_3x3x3,out_3x3x3,red_3x3x3,out2_3x3x3,out_1x1x1_pool):
        super(Inception_Block_v3,self).__init__()

        self.branch_1 = conv_block(in_channels,out_1x1x1,kernel_size=1)
        self.branch_2 = nn.Sequential(conv_block(in_channels,red1_3x3x3,kernel_size=1),conv_block(red1_3x3x3,red2_3x3x3,kernel_size=3,stride=1,padding=1),conv_block(red2_3x3x3,out_3x3x3,kernel_size=3,stride=1,padding=1))
        self.branch_3 = nn.Sequential(conv_block(in_channels,red_3x3x3,kernel_size=1),conv_block(red_3x3x3,out2_3x3x3,kernel_size=3,stride=1,padding=1))
        self.branch_4 = nn.Sequential(nn.MaxPool3d(kernel_size=3,stride=1,padding=1),conv_block(in_channels,out_1x1x1_pool,kernel_size=1))

    def forward(self,x):
        return torch.cat([self.branch_1(x),self.branch_2(x),self.branch_3(x),self.branch_4(x)],1)


class conv_block(nn.Module):
    def __init__(self,in_channels,out_channels,**kwargs):
        super(conv_block,self).__init__()
        self.relu = nn.ReLU()
        self.conv = nn.Conv3d(in_channels,out_channels,**kwargs)
        self.batchnorm = nn.BatchNorm3d(out_channels)

    def forward(self,x):
        return self.relu(self.batchnorm(self.conv(x)))

#Testing only
if __name__ == '__main__':
    net = InceptionNet_v1()
    if torch.cuda.device_count() > 0:
        summary(net.cuda(),(1,128,128,128))
    else:
        summary(net,(1,128,128,128))
    
