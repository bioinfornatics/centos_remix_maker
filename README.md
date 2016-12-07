# Centos remix maker

Is a basic python tool to generate a minimal centos iso from a given kickstart
The tool do not use a python library to parse command line option for compatibility reason.

## Usage

Is really simple: 

```
$ python centos_remix_maker/src/remix/main.py <ks.cfg> <myWorkDir> <version> <arch> <myIsoName>
```

All parameter are mandatory:
 - version is formated as: 6:3, 6.6, 7.0  and so on …
 - arch: x86_64 or i386

Not yet supported thing:
 - from  kickstart file
  * exclude package statement is ignored
  * mirrorlist parameter from repo line is ignored for this reason baseurl parameter is required

## Dependencies:
 - executable
  * sqlite
  * createrepo
  * mkisofs
 - python lib
  * Beautiful Soup 4
  * sqlite3
