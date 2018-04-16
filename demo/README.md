# Prerequisites

The demo script (`Drakefile`) provides an example on toy data for the
usage of our toolbox. Before running demo script, you need to install
the following tools:

1. The current version of `abbo-tools`
2. [LIBLINEAR](https://www.csie.ntu.edu.tw/~cjlin/liblinear/) needs to be installed
2. Drake (more information available at [https://github.com/Factual/drake](https://github.com/Factual/drake))

## Installing Drake

In order to execute the steps defined in the `Drakefile` you first
need to install the tool `Drake`. Drake is a data workflow tool which
allows you to organize command execution for data processing (`make`
for data). In particular, the user can define multiple data processing
steps along with their expected inputs/outputs. During execution of
the script, Drake will resolve all dependencies automatically and
execute the defined steps in the right order. In addition, drake
allows you to execute the steps separately from each other. It will
then only create the data which is necessary to execute a specified
step. 

To install Drake on OS X simply execute

```bash
brew install drake
```

To install Drake on Linux, you need to perform the following steps:

1. Download the `drake` script [https://raw.githubusercontent.com/Factual/drake/master/bin/drake](https://raw.githubusercontent.com/Factual/drake/master/bin/drake)
2. Add the script to your `$PATH` (e.g. `~/bin`)
3. Set it to be executable (`chmod +x ~/bin/drake`)
4. Run `drake`

## Running the Demo script

Change into the directory which contains the `Drakefile` and run

```bash
drake
```

This will show you an overview of all of all steps that will be executed. 
In order to proceed, type `y`.