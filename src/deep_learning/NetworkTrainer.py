import wandb
import torch


class NetworkTrainer:

    def __init__(self, nn_model, train_set_loader, val_set_loader, config):
        self.nn_model = nn_model
        self.train_set_loader = train_set_loader
        self.val_set_loader = val_set_loader
        self.loss_function = config.loss_function
        self.optimizer = config.optimizer
        self.config = config

    def start_training(self):
        wandb.watch(self.nn_model, self.loss_function, log='all', log_freq=50)

        mini_batches = 0
        loss_value = 0

        for epoch in range(self.config.num_epochs):
            for batch_id, (model, label) in enumerate(self.train_set_loader, 1):
                self.nn_model.train()

                if self.config.device.type == 'cuda':
                    model, label = model.cuda(), label
                else:
                    model, label = model, label

                output = self.nn_model(model)
                output = output.to(torch.float32)
                label = label.to(torch.float32)
                loss = self.loss_function(output, label)

                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()

                mini_batches += 1
                loss_value += float(loss)

                # Plotting in wandb
                if mini_batches % self.config.plot_frequency == 0:
                    val_loss = self.validation_phase(self.nn_model, self.val_set_loader, self.loss_function, epoch)
                    self.training_log(loss_value / self.config.plot_frequency, mini_batches)
                    self.training_log(val_loss, mini_batches, False)

                    path = "model.pt"
                    torch.save({'epoch': epoch, 'model_state_dict': self.nn_model.state_dict(),
                                'optimizer_state_dict': self.optimizer.state_dict(), 'loss': loss_value}, path)

                    loss_value = 0

                print('Epoch-{0} lr: {1:f}'.format(epoch, self.optimizer.param_groups[0]['lr']))

    def training_log(self, loss, mini_batch, train=True):
        if train:
            wandb.log({'batch': mini_batch, 'loss': loss})
        else:
            wandb.log({'batch': mini_batch, 'loss': loss})

    def validation_phase(self, nn_model, val_set_loader, loss_function, epoch):

        print(f"[INFO] Validating.")

        nn_model.eval()

        mini_batches = 0
        loss_val = 0

        for batch_id, (model, label) in enumerate(val_set_loader, 1):

            if self.config.device.type == 'cuda':
                model, label = model.cuda(), label
            else:
                model, label = model, label

            output = nn_model(model)
            loss = loss_function(output, label)

            mini_batches += 1
            loss_val += float(loss)

        loss_val = loss_val / mini_batches
        return loss_val