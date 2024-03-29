import numpy as np
import sklearn.preprocessing as prep
import tensorflow as tf

def xavier_init(n_input,n_output,constant=1):
    low = -constant * np.sqrt(6.0/(n_input+n_output))
    high = constant * np.sqrt(6.0/(n_input+n_output))
    return tf.random_uniform((n_input,n_output),minval=low,maxval=high,dtype=tf.float32)

class AdditiveGaussianNoiseAutoencoder(object):
    def __init__(self,n_input,n_hidden,transfer_function=tf.nn.softplus,optimizer=tf.train.AdamOptimizer(),scale=0.1):
        """
        n_input:输入变量数
        n_hidden:隐含层节点数
        transfer_function:隐含层激活函数
        optimizer:优化器
        scale：高斯噪声系数
        """
        self.n_input = n_input
        self.n_hidden = n_hidden
        self.transfer = transfer_function
        self.scale = tf.placeholder(dtype=tf.float32)
        self.training_scale = scale

        network_weights = self._initialize_weights()
        self.weights = network_weights

        self.x = tf.placeholder(tf.float32,[None,self.n_input])
        self.hidden = self.transfer(tf.add(tf.matmul(self.x+scale*tf.random_normal((n_input,)),self.weights['w1']),self.weights['b1']))
        self.reconstruction = tf.add(tf.matmul(self.hidden,self.weights['w2']),self.weights['b2'])
        
        self.cost = 0.5*tf.reduce_sum(tf.pow(tf.subtract(self.reconstruction, self.x),2.0))
        self.optimizer = optimizer.minimize(self.cost)

        init = tf.global_variables_initializer()
        self.sess = tf.Session()
        self.sess.run(init)

    def _initialize_weights(self):
        all_weights = dict()
        all_weights['w1'] = tf.Variable(xavier_init(self.n_input,self.n_hidden))
        all_weights['b1'] = tf.Variable(tf.zeros([self.n_hidden],dtype=tf.float32))
        all_weights['w2'] = tf.Variable(tf.zeros([self.n_hidden,self.n_input],dtype=tf.float32))
        all_weights['b2'] = tf.Variable(tf.zeros([self.n_input],dtype=tf.float32))
    
    def partial_fit(self,X):
        cost,opt = self.sess.run((self.cost,self.optimizer),
                                 feed_dict={self.x:X,
                                            self.scale:self.training_scale})
        return cost
    
    def calc_total_cost(self,X):
        return self.sess.run(self.cost,feed_dict={self.x:X,self.scale:self.training_scale})

    def transform(self,X):
        return self.sess.run(self.hidden,feed_dict={self.x:X,self.scale:self.training_scale})

    def generate(self,hidden=None):
        """将隐含层的输出结果作为输入，通过之后的重建层将提取到的高阶特征复原为原始数据
        
        Keyword Arguments:
            hidden {[type]} -- 隐藏层节点数 (default: {None})
        """
        if hidden == None:
            hidden = np.random.normal(size=self.weights['b1'])
        return self.sess.run(self.reconstruction,feed_dict={self.hidden:hidden})

    def reconstruct(self,X):
        return self.sess.run(self.reconstruction,feed_dict={self.x:X,self.scale:self.training_scale})
    
    def getWeights(self):
        return self.sess.run(self.weights['w1'])
    
    def getBiases(self):
        return self.sess.run(self.weights['b1'])


if __name__ == '__main__':
    data = input_data.read_data_sets(,one_hot=True)
    X_train,X_test = standard_scale() # 转换数据的规模，感觉不太需要
    n_samples = len() # 训练集样本数量
    training_epochs = 1
    batch_size = 128
    display_step = 1

    autoencoder = AdditiveGaussianNoiseAutoencoder(n_input=784,
                                                    n_hidden=200,
                                                    transfer_function=tf.nn.softplus,
                                                    optimizer=tf.train.AdamOptimizer(learning_rate=0.001),
                                                    scale=0.01)
    for epoch in range(training_epochs):
        avg_cost = 0.0
        total_batch = int(n_samples/batch_size)
        for i in range(total_batch):
            batch_xs = get_random_block_from_data(X_train,batch_size)
            cost = autoencoder.partial_fit(batch_xs)
            avg_cost += cost / n_samples * batch_size
        if epoch % display_step == 0:
            print('Epoch:','%04d'%(epoch+1),
                  'Cost=','{:.9f}'.format(avg_cost))
    print('Total cost:'+str(autoencoder.calc_total_cost(X_test)))
    # 用训练好的自编码器得到所有运动学片段的隐含层特征