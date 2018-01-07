import logging
import attr
import argparse
import torch
import torch.utils.data as data
import torch.optim as optim
import torch.nn as nn
import models
from torch.autograd import Variable
from chess_dataset import ChessDataset


@attr.s
class SupervisedTrainer():
    model = attr.ib()
    data = attr.ib()
    logger = attr.ib(default=logging.getLogger(__name__))
    log_interval = attr.ib(default=2000)
    batch_size = attr.ib(default=16)
    num_epochs = attr.ib(default=100)
    cuda = attr.ib(default=True)

    def __attrs_post_init__(self):
        self.cuda = self.cuda and torch.cuda.is_available()
        if self.cuda:
            self.logger.info('Using CUDA')
            self.model.cuda()

    def train(self):
        self.model.train(mode=True)
        dataset = ChessDataset(self.data)
        data_loader = data.DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=True
        )

        criterion = nn.CrossEntropyLoss()
        optimizer = optim.SGD(
            self.model.parameters(),
            lr=0.001,
            momentum=0.9,
            nesterov=True
        )

        for epoch in range(self.num_epochs):
            self.logger.info(f'Epoch {epoch}')

            running_loss = 0.0
            for i, d in enumerate(data_loader):
                # get the inputs
                inputs, labels = d

                # wrap them in Variable
                if self.cuda:
                    inputs = Variable(inputs.cuda())
                    labels = Variable(labels.cuda())
                else:
                    inputs = Variable(inputs)
                    labels = Variable(labels)

                # zero the parameter gradients
                optimizer.zero_grad()

                # forward + backward + optimize
                outputs = self.model(inputs)
                outputs = outputs.view(outputs.shape[0], -1)

                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()

                running_loss += loss.data[0]
                if i % self.log_interval == self.log_interval - 1:
                    avg_loss = running_loss / self.log_interval
                    self.logger.info('[%d, %5d] loss: %.3f' %
                                     (epoch, i, avg_loss))
                    running_loss = 0.0

        self.logger.info('Training finished')


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('model')
    parser.add_argument('data')
    parser.add_argument('-i', '--log-interval', type=int)
    parser.add_argument('-b', '--batch-size', type=int)
    parser.add_argument('-e', '--num-epochs', type=int)
    parser.add_argument('-c', '--cuda', type=bool)
    parser.add_argument('-l', '--log-file')

    args = parser.parse_args()

    logger = logging.getLogger('SupervisedTrainer')
    logging_config = {
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'level': logging.INFO,
    }
    if args.log_file:
        logging_config['filename'] = args.log_file
    logging.basicConfig(**logging_config)

    model = models.create(args.model)
    trainer_setting = {
        'model': model,
        'data': args.data,
        'logger': logger,
    }
    if args.log_interval:
        trainer_setting['log_interval'] = args.log_interval
    if args.batch_size:
        trainer_setting['batch_size'] = args.batch_size
    if args.num_epochs:
        trainer_setting['num_epochs'] = args.num_epochs
    if args.cuda:
        trainer_setting['cuda'] = args.cuda
    trainer = SupervisedTrainer(**trainer_setting)
    trainer.train()


if __name__ == '__main__':
    run()
