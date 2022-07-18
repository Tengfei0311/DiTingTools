import tensorflow as tf
from keras import Model, layers, optimizers
import keras.backend as K
import numpy as np
from keras.layers import Dense, Flatten, BatchNormalization, MaxPooling1D, LSTM
from keras.layers import Activation, add

def Conv1D_simple(x, t_channel_num,  activation_func='linear'):
    x_1 = layers.Conv1D(t_channel_num, 3, dilation_rate=1, activation=activation_func, padding='same')(x)
    return x_1

def ResBlock(x, t_channel_num, batch_norm = False, activation_func='linear'):
    x_in = x
    x_out = Conv1D_simple(x, t_channel_num, activation_func=None)
    if batch_norm:
        x = BatchNormalization()(x_out)
    x_out = Activation(activation_func)(x_out)
    x_out = Conv1D_simple(x_out, t_channel_num,  activation_func=None)
    if batch_norm:
        x = BatchNormalization()(x_out)
    x_out = Activation(activation_func)(x_out)
    x_out = add([x_in,x_out])

    return x_out

def Unet_downsampling_part(input_data, name=None):
    c_1_1 = Conv1D_simple(input_data, 8)
    c_1_2 = ResBlock(c_1_1, 8)

    p1 = MaxPooling1D(2,strides=2,padding='same')(c_1_2)
    c_2_1 = Conv1D_simple(p1, 16)
    c_2_2 = ResBlock(c_2_1, 16)

    p2 = MaxPooling1D(2,strides=2,padding='same')(c_2_2)
    c_3_1 = Conv1D_simple(p2, 32)
    c_3_2 = ResBlock(c_3_1, 32)

    p3 = MaxPooling1D(2,strides=2,padding='same')(c_3_2)
    c_4_1 = Conv1D_simple(p3, 64)
    c_4_2 = ResBlock(c_4_1, 64)

    p4 = MaxPooling1D(2,strides=2,padding='same')(c_4_2)
    c_5_1 = Conv1D_simple(p4, 128)
    c_5_2 = ResBlock(c_5_1, 128)

    return c_1_2, c_2_2, c_3_2, c_4_2, c_5_2

def DiTingMag_Basic(cfgs=None):
    """
    Stacked Unet
    """
    input_data = layers.Input(shape=(cfgs['Training']['Model']['length_before_P'] + cfgs['Training']['Model']['length_after_P'], cfgs['Training']['Model']['input_channel']),name='input')

    # stack 1 down part
    c_1_2, c_2_2, c_3_2, c_4_2, c_5_2 = Unet_downsampling_part(input_data, name='D_1')
    
    # stack 1 mag
    lstm_mag = LSTM(16, activation='tanh', return_sequences=True)(c_5_2)
    lstm_mag_output = LSTM(1, activation='tanh', return_sequences=True)(lstm_mag)

    model = Model(inputs=input_data,outputs=[lstm_mag_output])    

    if cfgs['Training']['Optimizer'] == 'adam':
        opt = optimizers.Adam(cfgs['Training']['LR'],clipvalue=5.0)
    else:
        pass

    model.compile(loss=cfgs['Training']['Loss'], optimizer=opt)
    
    model.summary()

    return model