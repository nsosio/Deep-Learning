# -*- coding: utf-8 -*-
"""
Created on Sun Jun 10 15:31:34 2018

@author: lucas
"""

import time
from keras.models import Model
from keras.layers import Input,Embedding, Conv1D, Activation, Dot, Lambda
from keras.callbacks import TensorBoard, EarlyStopping
import keras.backend as K
import tensorflow as tf


#%%

class ModelBuilder(object):
    
    def __init__(self, embeddings, q_length, x1, x2, y, dimensions):
        super(ModelBuilder, self).__init__()
        self.embeddings=embeddings
        self.vocabulary_size=embeddings.shape[0]
        self.embedding_size=embeddings.shape[1]
        self.q_length=q_length
        self.x1 = x1
        self.x2 = x2
        self.y = y
        self.dimensions = dimensions
        #self.clu=clu
        #self.window_size=window_size

    def embeddings_initialize(self, shape, dtype=None):
        assert shape==self.embeddings.shape
        return self.embeddings
        
    
    def buildModel(self, clu, window_size):
        q_1= Input(shape=(self.q_length,), dtype='int32')
        q_2= Input(shape=(self.q_length,), dtype='int32')    
        
        lookup=Embedding(self.vocabulary_size, self.embedding_size, input_length=self.q_length, embeddings_initializer=self.embeddings_initialize, trainable=False)
        lookup_layer_1= lookup(q_1)
        lookup_layer_2= lookup(q_2)
        
        conv1d=Conv1D(filters=clu, kernel_size=window_size, activation='tanh', padding='same')
        conv_layer_1=conv1d(lookup_layer_1)
        conv_layer_2=conv1d(lookup_layer_2)
        
        sum_layer_1=Lambda(lambda x: K.sum(x,axis=1))(conv_layer_1)
        sum_layer_2=Lambda(lambda x: K.sum(x,axis=1))(conv_layer_2)
        
        activation_1=Activation('tanh')(sum_layer_1)
        activation_2=Activation('tanh')(sum_layer_2)
        
        similarity_layer= Dot(axes=1, normalize=True, name='similarity')([activation_1,activation_2])
        
        #predictions = Lambda(lambda x: K.cast(x>=0.5, dtype='float32'), name='predictions')(similarity_layer)
        
        return Model(inputs=[q_1, q_2], outputs=similarity_layer)
        
    
    def compileModel(self,model):
        model.compile(loss= 'binary_crossentropy',
                      optimizer='adam',
                      metrics=['accuracy'])
                      

    def trainModel(self,model, x_1_train, x_2_train, labels, batch_size, num_epochs):
        sess = tf.Session()
        tf.summary.FileWriter('./logs/', sess.graph)
        # tensorboard --logdir=logs  for executing TensorBoard 
        # localhost:6006 to view the TensorBoard
        modelid = time.strftime("%Y%m%d%H%M%S")
        tensorboard = TensorBoard(log_dir='./logs/'+modelid, histogram_freq=0,
                              write_graph=True, write_images=True)
        early_stopping = EarlyStopping(patience=20)
        return model.fit(x=[x_1_train, x_2_train], 
                         y=labels, 
                         batch_size=batch_size, 
                         epochs=num_epochs,
                         validation_split=0.04,
                         callbacks = [tensorboard, early_stopping])
        
    def log_dir_name(self, window_size, clu):
        # The dir-name for the TensorBoard log-dir.
        s = "/wind_{0}_clu_{1}/"
    
        # Insert all the hyper-parameters in the dir-name.
        log_dir = s.format(window_size,
                           clu)
    
        return log_dir
    
    def fitness(self, window_size, clu, batch_size=128, num_epochs=1):
    
        # Print the hyper-parameters.
        print('window_size:', window_size)
        print('clu:', clu)
        print()
        
        global best_accuracy
        best_accuracy=0
        
        model = self.buildModel(window_size=window_size,
                             clu=clu)
        self.compileModel(model)
        log_dir = "./logs/" + self.log_dir_name(window_size, clu)
        
        tensorboard = TensorBoard(
            log_dir=log_dir,
            histogram_freq=0,
            write_graph=True,
            write_grads=False,
            write_images=False)
        early_stopping = EarlyStopping(patience=20)
       
        history = model.fit(x=[self.x1, self.x2],
                            y=self.y, 
                            batch_size=batch_size, 
                            epochs=num_epochs,
                            validation_split=0.04,
                            callbacks = [tensorboard, early_stopping])
    
        accuracy = max(history.history['val_acc'])
    
        print()
        print("Accuracy: {0:.2%}".format(accuracy))
        print()
    
    
        if accuracy > best_accuracy:
            model.save("best_model.h5")
            best_accuracy = accuracy
    
        del model
        
        K.clear_session()
        
        return -accuracy



