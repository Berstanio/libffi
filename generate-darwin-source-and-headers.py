#!/usr/bin/env python
import subprocess
import os
import errno
import collections
import glob
import argparse

class Platform(object):
    pass

class ios_simulator_platform(Platform):
    directory = 'darwin_ios'
    sdk = 'iphonesimulator'
    arch = 'i386'
    triple = 'i386-apple-darwin11'
    version_min = '-miphoneos-version-min=8.0'

    prefix = "#ifdef __i386__\n\n"
    suffix = "\n\n#endif"
    src_dir = 'x86'
    src_files = ['sysv.S', 'ffi.c']
    hdr_files = ['internal.h']


class ios_simulator64_platform(Platform):
    directory = 'darwin_ios'
    sdk = 'iphonesimulator'
    arch = 'x86_64'
    triple = 'x86_64-apple-darwin13'
    version_min = '-miphoneos-version-min=8.0'

    prefix = "#ifdef __x86_64__\n\n"
    suffix = "\n\n#endif"
    src_dir = 'x86'
    src_files = ['unix64.S', 'ffi64.c', 'ffiw64.c', 'win64.S']
    hdr_files = ['internal64.h', 'asmnames.h']


class ios_device_platform(Platform):
    directory = 'darwin_ios'
    sdk = 'iphoneos'
    arch = 'armv7'
    triple = 'arm-apple-darwin11'
    version_min = '-miphoneos-version-min=8.0'

    prefix = "#ifdef __arm__\n\n"
    suffix = "\n\n#endif"
    src_dir = 'arm'
    src_files = ['sysv.S', 'ffi.c']
    hdr_files = ['internal.h']


class ios_device64_platform(Platform):
    directory = 'darwin_ios'
    sdk = 'iphoneos'
    arch = 'arm64'
    triple = 'aarch64-apple-darwin13'
    version_min = '-miphoneos-version-min=8.0'

    prefix = "#ifdef __arm64__\n\n"
    suffix = "\n\n#endif"
    src_dir = 'aarch64'
    src_files = ['sysv.S', 'ffi.c']
    hdr_files = ['internal.h']


class tvos_simulator64_platform(Platform):
    directory = 'darwin_tvos'
    sdk = 'appletvsimulator'
    arch = 'x86_64'
    triple = 'x86_64-apple-darwin13'
    version_min = '-mappletvos-version-min=9.0'

    prefix = "#ifdef __x86_64__\n\n"
    suffix = "\n\n#endif"
    src_dir = 'x86'
    src_files = ['unix64.S', 'ffi64.c']
    hdr_files = ['internal64.h']


class tvos_device64_platform(Platform):
    directory = 'darwin_tvos'
    sdk = 'appletvos'
    arch = 'arm64'
    triple = 'aarch64-apple-darwin13'
    version_min = '-mappletvos-version-min=9.0'

    prefix = "#ifdef __arm64__\n\n"
    suffix = "\n\n#endif"
    src_dir = 'aarch64'
    src_files = ['sysv.S', 'ffi.c']
    hdr_files = ['internal.h']


class desktop_amd64_platform(Platform):
    directory = 'darwin_osx'
    sdk = 'macosx'
    arch = 'x86_64'
    triple = 'x86_64-apple-darwin10'
    version_min = '-mmacosx-version-min=10.6'

    prefix = "#ifdef __x86_64__\n\n"
    suffix = "\n\n#endif"
    src_dir = 'x86'
    src_files = ['unix64.S', 'ffi64.c', 'ffiw64.c', 'win64.S']
    hdr_files = ['internal64.h', 'asmnames.h']


class desktop_arm64_platform(Platform):
    directory = 'darwin_osx'
    sdk = 'macosx'
    arch = 'arm64'
    triple = 'aarch64-apple-darwin20'
    version_min = '-mmacosx-version-min=11.0'

    prefix = "#ifdef __arm64__\n\n"
    suffix = "\n\n#endif"
    src_dir = 'aarch64'
    src_files = ['sysv.S', 'ffi.c']
    hdr_files = ['internal.h']


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno != errno.EEXIST:
            raise


def move_file(src_dir, dst_dir, filename, file_suffix=None, prefix='', suffix=''):
    mkdir_p(dst_dir)
    out_filename = filename

    if file_suffix:
        if filename in ['internal64.h', 'asmnames.h', 'internal.h']:
            out_filename = filename
        else:
            split_name = os.path.splitext(filename)
            out_filename = "%s_%s%s" % (split_name[0], file_suffix, split_name[1])

    with open(os.path.join(src_dir, filename)) as in_file:
        with open(os.path.join(dst_dir, out_filename), 'w') as out_file:
            if prefix:
                out_file.write(prefix)

            out_file.write(in_file.read())

            if suffix:
                out_file.write(suffix)


def list_files(src_dir, pattern=None, filelist=None):
    if pattern: filelist = glob.iglob(os.path.join(src_dir, pattern))
    for file in filelist:
        yield os.path.basename(file)


def copy_files(src_dir, dst_dir, pattern=None, filelist=None, file_suffix=None, prefix=None, suffix=None):
    for filename in list_files(src_dir, pattern=pattern, filelist=filelist):
        move_file(src_dir, dst_dir, filename, file_suffix=file_suffix, prefix=prefix, suffix=suffix)


def copy_src_platform_files(platform):
    src_dir = os.path.join('src', platform.src_dir)
    dst_dir = os.path.join(platform.directory, 'src', platform.src_dir)
    copy_files(src_dir, dst_dir, filelist=platform.src_files, file_suffix=platform.arch, prefix=platform.prefix, suffix=platform.suffix)
    copy_files(src_dir, dst_dir, filelist=platform.hdr_files, file_suffix=None, prefix=platform.prefix, suffix=platform.suffix)


def build_target(platform, platform_headers):
    def xcrun_cmd(cmd):
        return 'xcrun -sdk %s %s -arch %s' % (platform.sdk, cmd, platform.arch)

    tag='%s-%s' % (platform.sdk, platform.arch)
    build_dir = 'build_%s' % tag
    mkdir_p(build_dir)
    env = dict(CC=xcrun_cmd('clang'),
               LD=xcrun_cmd('ld'),
               CFLAGS='%s -fembed-bitcode' % (platform.version_min))
    working_dir = os.getcwd()
    try:
        os.chdir(build_dir)
        subprocess.check_call(['../configure', '-host', platform.triple], env=env)
    finally:
        os.chdir(working_dir)
    for src_dir in [build_dir, os.path.join(build_dir, 'include')]:
        copy_files(src_dir,
                   os.path.join(platform.directory, 'include'),
                   pattern='*.h',
                   file_suffix=platform.arch,
                   prefix=platform.prefix,
                   suffix=platform.suffix)

        for filename in list_files(src_dir, pattern='*.h'):
            platform_headers[filename].add((platform.prefix, platform.arch, platform.suffix))


def generate_source_and_headers(generate_osx=True, generate_ios=True, generate_tvos=False):
    copy_files('src', 'darwin_common/src', pattern='*.c')
    copy_files('include', 'darwin_common/include', pattern='*.h')

    if generate_ios:
        # copy_src_platform_files(ios_simulator_platform)
        copy_src_platform_files(ios_simulator64_platform)
        copy_src_platform_files(ios_device_platform)
        copy_src_platform_files(ios_device64_platform)
    if generate_tvos:
        copy_src_platform_files(tvos_simulator64_platform)
        copy_src_platform_files(tvos_device64_platform)
    if generate_osx:
        copy_src_platform_files(desktop_amd64_platform)
        copy_src_platform_files(desktop_arm64_platform)

    platform_headers = collections.defaultdict(set)

    if generate_ios:
        # build_target(ios_simulator_platform, platform_headers)
        build_target(ios_simulator64_platform, platform_headers)
        build_target(ios_device_platform, platform_headers)
        build_target(ios_device64_platform, platform_headers)
    if generate_tvos:
        build_target(tvos_simulator64_platform, platform_headers)
        build_target(tvos_device64_platform, platform_headers)
    if generate_osx:
        build_target(desktop_amd64_platform, platform_headers)
        build_target(desktop_arm64_platform, platform_headers)

    mkdir_p('darwin_common/include')
    for header_name, tag_tuples in platform_headers.items():
        basename, suffix = os.path.splitext(header_name)
        with open(os.path.join('darwin_common/include', header_name), 'w') as header:
            for tag_tuple in tag_tuples:
                header.write('%s#include <%s_%s%s>\n%s\n' % (tag_tuple[0], basename, tag_tuple[1], suffix, tag_tuple[2]))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--disable-ios', action='store_true', default=False)
    parser.add_argument('--disable-tvos', action='store_true', default=False)
    parser.add_argument('--disable-osx', action='store_true', default=False)
    args = parser.parse_args()

    generate_source_and_headers(generate_osx=not args.disable_osx, generate_ios=not args.disable_ios, generate_tvos=False)
