import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data
from PIL import Image
from numpy import random, expand_dims, uint8, array, shape

from StringIO import StringIO

MNIST = input_data.read_data_sets("./MNIST_data/", one_hot = True)

def digit(id):
  record = MNIST.test.images[id]
  array = record.reshape((28, 28))
  return Image.fromarray(uint8(255 * (1.0 - array)))

# Maybe consolidate these two functions? Both return an MNIST input vector
def mnist_array(blob):
  bytes = bytearray(blob)
  image = Image.open(StringIO(bytes))
  image.thumbnail((28, 28), Image.ANTIALIAS)
  image.convert("L")
  image_array = array(image)[:,:,3] / 255.0
  return image_array.reshape((784,))

def mnist_input(id):
  return MNIST.test.images[id]


class MnistNetwork:
  def __init__(self):
    self.build()

  def build(self):
    tf.reset_default_graph()
    self.PROB = tf.placeholder(tf.float32)

    def layer(inputs, kernel_shape, bias_shape, multiply, activate):
      self.weights = tf.get_variable(
        "weights",
        kernel_shape,
        initializer = tf.random_normal_initializer()
      )
      self.biases = tf.get_variable(
        "biases",
        bias_shape,
        initializer = tf.constant_initializer(0.0)
      )
      return activate(multiply(inputs, self.weights) + self.biases)

    def max_pool(h):
      return tf.nn.max_pool(
          h,
          ksize = [1, 2, 2, 1],
          strides = [1, 2, 2, 1],
          padding = 'SAME'
      )

    def conv(inputs, weights):
      return tf.nn.conv2d(
          inputs,
          weights,
          strides = [1, 1, 1, 1],
          padding = 'SAME'
      )

    def flatten(h):
      return tf.reshape(h, [-1, 7 * 7 * 64])

    def dropout(h, keep_prob):
      return tf.nn.dropout(h, keep_prob)

    def apply_network(inputs):
      with tf.variable_scope("conv1") as scope:
        activate = lambda a: max_pool(tf.nn.relu(a))
        layer1 = layer(inputs, [5, 5, 1, 32], [32], conv, activate)
        scope.reuse_variables()

      with tf.variable_scope("conv2") as scope:
        activate = lambda a: flatten(max_pool(tf.nn.relu(a)))
        layer2 = layer(layer1, [5, 5, 32, 64], [64], conv, activate)
        scope.reuse_variables()

      with tf.variable_scope("conn1"):
        activate = lambda a: dropout(tf.nn.relu(a), self.PROB)
        layer3 = layer(layer2, [7 * 7 * 64, 1024], [1024], tf.matmul, activate)
        scope.reuse_variables()

      with tf.variable_scope("conn2"):
        activate = lambda a: a
        output_layer = layer(layer3, [1024, 10], [10], tf.matmul, activate)
        scope.reuse_variables()
        return output_layer

    self.x = tf.placeholder(tf.float32, shape = [None, 784])
    self.y_ = tf.placeholder(tf.float32, shape = [None, 10])
    self.x_image = tf.reshape(self.x, [-1, 28, 28, 1])

    with tf.variable_scope("images") as scope:
      try:
        self.predict_operation = apply_network(self.x_image)
      except ValueError:
        scope.reuse_variables()
        self.predict_operation = apply_network(self.x_image)

    self.saver = tf.train.Saver()

  def predict(self, input):
    with tf.Session() as session:
      self.saver.restore(session, './tutorial-variables.ckpt')
      # id = id or random.randint(0, 10000)
      # datum = expand_dims(MNIST.test.images[id], axis = 0)
      datum = expand_dims(input, axis = 0)
      output = session.run(
        self.predict_operation,
        feed_dict = { self.x: datum, self.PROB: 1.0 }
      )
      (prediction,) = [ p for p in tf.argmax(output, 1).eval() ]
      session.close()
      return prediction
