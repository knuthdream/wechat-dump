#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from PIL import Image
import io
import glob
import os
import numpy as np
import logging
import sqlite3
logger = logging.getLogger(__name__)

from common.textutil import ensure_unicode, md5


class AvatarReader(object):
    def __init__(self, res_dir, avt_db="avatar.index"):
        self.sfs_dir = os.path.join(res_dir, 'sfs')

        # new location of avatar, see #50
        self.avt_dir = os.path.join(res_dir, 'avatar')
        self.avt_db = avt_db
        self._use_avt = True
        if os.path.isdir(self.avt_dir) and len(os.listdir(self.avt_dir)):
            self.avt_use_db = False
        elif self.avt_db is not None \
                and os.path.isfile(self.avt_db) \
                and glob.glob(os.path.join(self.sfs_dir, 'avatar*')):
            self.avt_use_db = True
        else:
            logger.warn(
                    "Cannot find avatar files. Will not use avatar!")
            self._use_avt = False

    def get_avatar(self, username):
        """ username: `username` field in db.rcontact"""
        if not self._use_avt:
            return None
        username = ensure_unicode(username)
        avtid = md5(username.encode('utf-8'))
        dir1, dir2 = avtid[:2], avtid[2:4]
        candidates = glob.glob(os.path.join(self.avt_dir, dir1, dir2, f"*{avtid}*"))
        default_candidate = os.path.join(self.avt_dir, dir1, dir2, f"user_{avtid}.png")
        candidates.append(default_candidate)

        def priority(s):
            if "_hd" in s and s.endswith(".png"):
                return 10
            else:
                return 1

        candidates = sorted(set(candidates), key=priority, reverse=True)

        for cand in candidates:
            try:
                if self.avt_use_db:
                    pos, size = self.query_index(cand)
                    return self.read_img(pos, size)
                else:
                    if os.path.exists(cand):
                        if cand.endswith(".bm"):
                            return self.read_bm_file(cand)
                        else:
                            return Image.open(cand)
            except Exception:
                logger.exception("HHH")
                pass
        logger.warning("Avatar for {} not found in avatar database.".format(username))

    def read_img(self, pos, size):
        file_idx = pos >> 32
        fname = os.path.join(self.sfs_dir,
                'avatar.block.' + '{:05d}'.format(file_idx))
        # a 64-byte offset of each block file
        start_pos = pos - file_idx * (2**32) + 64
        try:
            with open(fname, 'rb') as f:
                f.seek(start_pos)
                data = f.read(size)
                im = Image.open(io.BytesIO(data))
                return im
        except IOError as e:
            logger.warn("Cannot read avatar from {}: {}".format(fname, str(e)))
            return None

    def read_bm_file(self, fname):
        # history at https://github.com/ppwwyyxx/wechat-dump/pull/14
        with open(fname, 'rb') as f:
            # filesize is 36880=96x96x4+16
            size = (96, 96, 3)
            img = np.zeros(size, dtype='uint8')
            for i in range(96):
                for j in range(96):
                    r, g, b, a = f.read(4)
                    img[i,j] = (r, g, b)
            return Image.fromarray(img, mode="RGB")

    def query_index(self, filename):
        conn = sqlite3.connect(self.avt_db)
        cursor = conn.execute("select Offset,Size from Index_avatar where FileName='{}'".format(filename))
        pos, size = cursor.fetchone()
        return pos, size

if __name__ == '__main__':
    import sys
    r = AvatarReader(sys.argv[1], sys.argv[2])
    print(r.get_avatar(sys.argv[3]))
