# TFTP

[![Component Registry](https://components.espressif.com/components/mr9you/rt-tftp/badge.svg)](https://components.espressif.com/components/mr9you/rt-tftp)

This component provides TFTP (Trivial File Transfer Protocol) server and client functionality for ESP-IDF platform. It's a port version of RT-Thread's [tftp](https://github.com/RT-Thread-packages/netutils/tree/master/tftp). It's simple, so there are no special documents for this component, just read the code.

## Add component to your project
Please use the component manager command `add-dependency` to add this component to your project's dependency. During the CMake step, the component will be downloaded automatically.

```shell
idf.py add-dependency "mr9you/rt-tftp=*"
```

## Examples
Please use the component manager command `create-project-from-example` to create a project from the example template.

```shell
idf.py create-project-from-example "mr9you/rt-tftp=*:tftp"
```

The example will then be downloaded into the current folder, where you can navigate into it for building and flashing.
