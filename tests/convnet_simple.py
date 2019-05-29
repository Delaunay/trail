import torch
import torch.nn as nn
import torch.optim
import torchvision.transforms as transforms
import torchvision.datasets as datasets
import torchvision.models as models

#from apex import amp
from trail import Experiment

# ----
import argparse
parser = argparse.ArgumentParser(description='Convnet training for torchvision models')

parser.add_argument('--batch-size', '-b', type=int, help='batch size', default=1)
parser.add_argument('--cuda', action='store_true', dest='cuda', default=True, help='enable cuda')
parser.add_argument('--no-cuda', action='store_false', dest='cuda', help='disable cuda')

parser.add_argument('--workers', '-j', type=int, default=4, help='number of workers/processors to use')
parser.add_argument('--seed', '-s', type=int, default=0, help='seed to use')
parser.add_argument('--epochs', '-e', type=int, default=5, help='number of epochs')

parser.add_argument('--arch', '-a', metavar='ARCH', default='resnet18')
parser.add_argument('--lr', '--learning-rate', default=0.1, type=float, metavar='LR')
parser.add_argument('--opt-level', type=str)

parser.add_argument('data', metavar='DIR', help='path to dataset')

# ----
exp = Experiment(__file__)
args = exp.get_arguments(parser, show=True)
device = exp.get_device()
chrono = exp.chrono()

try:
    import torch.backends.cudnn as cudnn
    cudnn.benchmark = True
except:
    pass


# ----
model = models.__dict__[args.arch]()
model = model.to(device)

criterion = nn.CrossEntropyLoss().to(device)

optimizer = torch.optim.SGD(
    model.parameters(),
    args.lr)

# ----
# model, optimizer = amp.initialize(
#     model,
#     optimizer,
#     enabled=args.opt_level != 'O0',
#     cast_model_type=None,
#     patch_torch_functions=True,
#     keep_batchnorm_fp32=None,
#     master_weights=None,
#     loss_scale="dynamic",
#     opt_level=args.opt_level
# )


# ----
train_dataset = datasets.ImageFolder(
    args.data,
    transforms.Compose([
        transforms.RandomResizedCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        ),
    ])
)

# ----
train_loader = torch.utils.data.DataLoader(
    train_dataset,
    batch_size=args.batch_size,
    shuffle=True,
    num_workers=args.workers,
    pin_memory=True
)

# dataset is reduced but should be big enough for benchmark!
batch_iter = None iter(train_loader)


def next_batch(batch_iter):
    try:
        input, target = next(batch_iter)
        input = input.to(device)
        target = target.to(device)
        return input, target

    except StopIteration:
        return None


model.train()
for epoch in range(args.epochs):
    batch_iter = iter(train_loader)

    with chrono.time('epoch_time') as epoch_time:
        batch_id = 0
        while True:
            with chrono.time('batch_time') as batch_time:

                with chrono.time('batch_wait'):
                    batch = next_batch(batch_iter)

                if batch is None:
                    break

                with chrono.time('batch_compute'):
                    input, target = batch

                    output = model(input)
                    loss = criterion(output, target)

                    exp.log_batch_loss(loss.item())

                    # compute gradient and do SGD step
                    optimizer.zero_grad()

                    # with amp.scale_loss(loss, optimizer) as scaled_loss:
                    #    scaled_loss.backward()
                    loss.backward()

                    optimizer.step()
                    batch_id += 1
            # ---
            exp.show_batch_eta(batch_id, args.epochs, epoch_time, throttle=None, every=60)
        # ---
    exp.show_epoch_eta(epoch, args.epochs, epoch_time)

exp.report()
