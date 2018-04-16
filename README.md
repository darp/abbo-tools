# ABBO Toolbox

This toolbox has been implemented as part of the project [Analyse und
Bekämpfung von bandenmäßigem Betrug im Onlinehandel
(ABBO)](http://www.abbo-projekt.de/). The project was funded by the
German Federal Ministry of Education and Research and aimed to impede
the success of organized fraud targeting online retailers.

## Installation

Ubuntu 12.04 LTS:

The ABBO toolbox uses [Cython](http://cython.org/). Therefore, you
first need to install:

```bash
sudo apt-get install python-dev g++
pip install cython
```

Once you have installed these packages, you can compile the `Cython`
code and finally install the ABBO toolbox with

```bash
python setup.py build_ext -i
python setup.py install
```

## Usage

In the following, we present some examples of the usage of the toolbox. 
An overview of all available modules can be displayed with 
`abbo_cli.py --help`. Furthermore, a demo of the tool can be found in
the `demo` directory.

### Data Generation

The tool allows creating artificial toy data which can be used to
examine attacks on the pseudonymization method. In particular, the
data is derived from several marginal distributions (mostly German
name distributions) stored in `abbo-tools/modules/generate/data`. 

The following command creates a random dataset with 100 entries:

```bash
abbo_cli generate -c 50 -n 100 example.json
```

This will create 100 orders from 50 different customers and store them
in JSON format. Note that in this example, multiple orders can be
assigned to the same customer. In case you require unique assignments,
you can use the `--unique_customers` option.

### Pseudonymization

The data set created in the previous step can now be pseudonymized. To
do so, we use the `pseudonymization` module of the toolbox. For
instance, we can pseudonymize the data using Bloom filters with a
length of 4000 Bits (`-m 4000`):

```bash
abbo_cli pseudonymize -m 4000 -d colored -n 3 -k 3 -t keyed -e KEY
example.json example.dat
```

In this example, the orders are first decomposed using a `colored
3-gram decomposition` (`-d colored` and `-n 3`). Subsequently, the
resulting elements are inserted into the Bloom filters using 3 keyed
hash functions (`-k 3` and `-t keyed`) where the used key is defined
by the `-e` option. 

A full list of available options can be displayed with `abbo_cli.py
pseudonymize --help`.

### Hardening Bloom filters

We can further improve the pseudonymization strength of the Bloom
filter by applying the mechanisms implemented in the `hardening`
module. In particular, it is possible to `add noise` to the filters or
`merge` them to decrease the probability of a de-pseudonymization.

```bash
abbo_cli hardening -l 3 -n 50 example.dat harden.dat
```

This will merge groups of three filters (`-l 3`) and add fifty percent
noise (`-n 50`) to the resulting filter.

### Converting to LIBSVM format

The toolbox also provides a module to convert data into the LIBSVM
format. This can be helpful in order to apply common machine learning
tools like [LIBSVM](https://www.csie.ntu.edu.tw/~cjlin/libsvm/) or [LIBLINEAR](https://www.csie.ntu.edu.tw/~cjlin/liblinear/).

```bash
abbo_cli convert example.dat example.libsvm
```

### Fraud Prediction

Finally, the toolbox allows predicting fraud using a linear SVM model.
Please note that the provided model is for demonstration purposes only
since it has been trained on toy data. However, the model can easily
be replaced by a model trained on actual data. An example on how to 
train and use a (simple) custom model can be found in the `demo` 
directory.
