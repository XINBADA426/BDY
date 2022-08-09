#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Chaobo Ren
# @Date:   2022/7/15 9:49
# @Last Modified by:   Ming
# @Last Modified time: 2022/7/15 9:49
import logging
import sys
from pathlib import Path

BASEPATH = Path(__file__)
sys.path.append(str(BASEPATH.absolute().parent.joinpath("lib")))
from BaiDuYunPan import BDYP
import click

#### Some Functions and global variable
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
__version__ = 'v0.0.4'


########################


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.version_option(version=__version__)
def cli():
    """
    Tools for deal with fasta file
    """
    pass


@click.command()
@click.option('--local',
              type=click.Path(),
              required=True,
              help='The local file to upload')
@click.option('--remote',
              type=click.Path(),
              required=True,
              help='The remote path')
@click.option('-t', '--thread',
              default=8,
              type=int,
              help='The thread to use')
@click.option('--ssl-check/--no-ssl-check',
              default=True,
              show_default=True,
              help='Whether verify host SSL cerificate')
@click.option('--force/--no-force',
              default=False,
              show_default=True,
              help='Whether force upload file')
def upload(local, remote, thread, ssl_check, force):
    """
    文件上传工具
    """
    session = BDYP(thread=thread, ssl_check=ssl_check)
    if force:
        logging.warning("强制使用单文件上传，可能会失败，请注意检查md5值")
        session.upload_single_force(local, remote)
    else:
        session.upload(local, remote)


cli.add_command(upload)

#### Main
if __name__ == "__main__":
    cli()
