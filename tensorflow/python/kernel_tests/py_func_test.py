# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Tests for py_func op."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow.python.platform

import numpy as np
import tensorflow as tf

from tensorflow.python.framework import errors
from tensorflow.python.ops import script_ops


class PyOpTest(tf.test.TestCase):

  def testBasic(self):

    def my_func(x, y):
      return np.sinh(x) + np.cosh(y)

    # scalar
    with self.test_session():
      x = tf.constant(1.0, tf.float32)
      y = tf.constant(2.0, tf.float32)
      z = tf.py_func(my_func, [x, y], [tf.float32])
      self.assertEqual(z[0].eval(), my_func(1.0, 2.0).astype(np.float32))

    # array
    with self.test_session():
      x = tf.constant([1.0, 2.0], tf.float64)
      y = tf.constant([2.0, 3.0], tf.float64)
      z = tf.py_func(my_func, [x, y], [tf.float64])
      self.assertAllEqual(
          z[0].eval(),
          my_func([1.0, 2.0], [2.0, 3.0]).astype(np.float64))

    # a bit exotic type (complex64)
    with self.test_session():
      x = tf.constant(1+2j, tf.complex64)
      y = tf.constant(3+4j, tf.complex64)
      z, = tf.py_func(my_func, [x, y], [tf.complex64])
      self.assertAllClose(z.eval(), my_func(1+2j, 3+4j))

    # a bit excotic function (rfft)
    with self.test_session():
      x = tf.constant([1., 2., 3., 4.], tf.float32)
      def rfft(x):
        return np.fft.rfft(x).astype(np.complex64)
      y, = tf.py_func(rfft, [x], [tf.complex64])
      self.assertAllClose(y.eval(), np.fft.rfft([1., 2., 3., 4.]))

    # returns a python literal.
    with self.test_session():
      def literal(x):
        return 1.0 if x == 0.0 else 0.0
      x = tf.constant(0.0, tf.float64)
      y, = tf.py_func(literal, [x], [tf.float64])
      self.assertAllClose(y.eval(), 1.0)

  def testLarge(self):
    with self.test_session() as sess:
      x = tf.zeros([1000000], dtype=np.float32)
      y = tf.py_func(lambda x: x + 1, [x], [tf.float32])
      z = tf.py_func(lambda x: x * 2, [x], [tf.float32])
      for _ in xrange(100):
        sess.run([y[0].op, z[0].op])

  def testCleanup(self):
    for _ in range(1000):
      g = tf.Graph()
      with g.as_default():
        c = tf.constant([1.], tf.float32)
        _ = tf.py_func(lambda x: x + 1, [c], [tf.float32])
    self.assertTrue(script_ops._py_funcs.size() < 100)

  def testError(self):
    with self.test_session():
      def bad(_):
        return tf.float32  # a python object. We should fail.
      x = tf.constant(0.0, tf.float64)
      y, = tf.py_func(bad, [x], [tf.float64])
      with self.assertRaisesRegexp(errors.UnimplementedError,
                                   "Unsupported numpy type"):
        y.eval()


if __name__ == "__main__":
  tf.test.main()
