# DividedPKG

A library and tool for modifying Indivisible's `.pkg` files.

## CLI usage

This is all meant for Windows. It might work on other platforms but if you're using those you're probably smart enough to adapt things on your own.

### Setup

```ps1
> py -m venv venv
> .\venv\Scripts\Activate.ps1
> python -m pip install -r requirements.txt
> python setup.py build_ext --inplace
```

### Patching your exe

This is required in order to run the game with modified `.pkg` files. Your output should look something like this.

```ps1
> python patch_exe.py path\to\Indivisible.exe
Searching for locations...
Replacement at $002d5d3b: 33 c0 90
Replacement at $002d5d73: 33 c0 90
Replacement at $002d5d8f: b8 00 00 00 00
Patch written
```

### List files in a pkg

```ps1
> python -m dividedpkg -l path\to\Indivisible\pkgs\data_8.pkg
```

### Unpack a pkg

```ps1
> python -m dividedpkg -u path\to\Indivisible\pkgs\data_8.pkg
```

Or filter it to a single file you saw in the listing (you must use `/` in this for paths, not `\`)

```ps1
> python -m dividedpkg -i TA_1000_1.dds -u path\to\Indivisible\pkgs\data_8.pkg
```

### Pack an edited file into the pkg

For this file, even though it's not compressed on disk, adding `.lz4` to the file name will cause the tool to compress it appropriately when re-importing it.

```ps1
> python -m dividedpkg -p path\to\Indivisible\pkgs\data_8\lz4\UI\Win\Textures\TA_1000_1.dds.lz4 path\to\Indivisible\pkgs\data_8.pkg
```

### Other commands

```ps1
# Create a new .pkg from a folder
> python -m dividedpkg -p folder

# Create a new .pkg from a list of files
> python -m dividedpkg -p file1 file2 new.pkg

# Repack all files that already exist in the .pkg
# This ignores other files you added, but no efficiency
# boost for unchanged files, they're all recompressed and etc
> python -m dividedpkg -p data_8
# or
> python -m dividedpkg -p data_8 data_8.pkg

# Unpack a pkg to another folder (folder must exist)
# contents dumped directly into "elsewhere"
> python -m dividedpkg -u data_8.pkg path\to\elsewhere

# Unpack all your .pkgs, will create a folder named after each pkg
> python -m dividedpkg -u *.pkg .

# Just decrypt and encrypt (rarely useful)
> python -m dividedpkg -d data_1.pkg
> python -m dividedpkg -e data_1_decrypted.pkg

# Other help
> python -m dividedpkg -h
usage: DividedPKG [-h] [--unpack | --pack | --list] [--decrypt | --encrypt]
                  [--include INCLUDE] [--exclude EXCLUDE]
                  [--compress-include COMPRESS_INCLUDE]
                  [src ...] dest

Packer and unpacker for Indivisible game

positional arguments:
  src
  dest

options:
  -h, --help            show this help message and exit
  --unpack, -u          Unpack the given pkg file(s) to the given directory       
  --pack, -p            Pack the given directory or file(s) into the given pkg    
                        file
  --list, -l            List the contents of the given pkg file(s)
  --decrypt, -d         Decrypt the given pkg file(s)
  --encrypt, -e         Encrypt the given pkg file(s)
  --include INCLUDE, -i INCLUDE
                        Include only files which match this glob (can be
                        specified multiple times)
  --exclude EXCLUDE, -x EXCLUDE
                        Exclude any files which match this glob (can be
                        specified multiple times)
  --compress-include COMPRESS_INCLUDE, -c COMPRESS_INCLUDE
                        Compress files which match this glob (can be specified
                        multiple times). Only used with --pack when creating a
                        pkg file from scratch.
```

All commands except pack support acting on multiple pkgs at once.

## Copyrights

* liblz4 files use a BSD 2-Clause license included in the respective files (not included in the .lib but still applies to it)
* key.dat is "owned" by Indivisible but is randomly generated data so ?
* key information from Ekey
* format information aluigi (Luigi Auriemma)
* everything else is by me, Kadalyn, and is released to the public domain
  * if you want to contibute to this repo, understand your work will also be released to the public domain
  * otherwise you may maintain your own fork
