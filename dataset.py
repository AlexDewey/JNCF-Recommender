from torch.utils.data import Dataset
from torch.utils.data.dataset import T_co
import torch


class RatingMatrixDataset(Dataset):

    # Init functions as a simple standard setup preparation of data by creating the user and item matricies.
    # For implementations that save data, saving the data past this initial init is computationally effective.
    def __init__(self, destinations, neg_size):
        # Import data
        import pandas as pd
        COLS = ['user_id', 'movie_id', 'rating', 'timestamp']
        data = None
        for destination in destinations:
            if data is None:
                data = pd.read_csv(destination, sep='\t', names=COLS).astype(int)
            else:
                new_data = pd.read_csv(destination, sep='\t', names=COLS).astype(int)
                data = pd.concat([data, new_data], axis=0)

        data['rating'] = data['rating'] / 5
        data = data.reset_index()

        # Create (num of users) 1x(num of movies) vectors to represent users
        self.user_matrix = torch.zeros(943, 1682)
        self.item_matrix = torch.zeros(1682, 943)
        for index, row in data.iterrows():
            self.user_matrix[int(row['user_id']) - 1][int(row['movie_id']) - 1] = row['rating']
            self.item_matrix[int(row['movie_id']) - 1][int(row['user_id'] - 1)] = row['rating']

        # Creating max value of every user rating. Normally 1, but on occasion lower.
        self.user_max = torch.max(self.user_matrix, dim=1)

        # For negative set later on
        self.neg_size = neg_size
        self.negative_set = None

    def __getitem__(self, idx):
        # Getting item index and rated item
        y = torch.where(self.user_matrix[idx] != 0)
        z = torch.randperm(y[0].shape[0])
        item_idx = int(y[0][int(z[0])])

        # Getting negative set for each item
        negative_set = torch.zeros(self.item_matrix.shape[0], self.neg_size)
        y_2 = torch.where(self.user_matrix[idx] == 0)
        z_2 = torch.randperm(y_2[0].shape[0])
        item_idx_2 = torch.searchsorted(y_2[0], z_2[0:self.neg_size])
        negative_set = [self.item_matrix[i, :] for i in item_idx_2]
        negative_set = torch.stack(negative_set)

        # Giving a version of the tensors that removes the value while not altering the original matrix
        user = self.user_matrix[idx].clone().detach()
        user[item_idx] = torch.tensor(0)
        item = self.item_matrix[item_idx].clone().detach()
        item[idx] = torch.tensor(0)

        # User rated items, item matrix for item, item id, negative set, user rating
        return user, item, item_idx, negative_set, self.user_matrix[idx][item_idx]

    # Simple return length
    def __len__(self):
        return len(self.user_matrix)

    def get_matricies(self):
        return self.user_matrix, self.item_matrix
