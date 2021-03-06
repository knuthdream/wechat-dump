#!/bin/bash
# File: android-interact.sh
# Date: Wed Nov 29 02:19:00 2017 -0800

PROG_NAME=`python -c "import os, sys; print(os.path.realpath(sys.argv[1]))" "$0"`
PROG_DIR=`dirname "$PROG_NAME"`
cd "$PROG_DIR"

# Please check that your path is the same, since this might be different among devices
RES_DIR="/mnt/sdcard/tencent/MicroMsg"
MM_DIR="/data/data/com.tencent.mm"

echo "Starting rooted adb server..."
adb root

if [[ $1 == "db" || $1 == "res" ]]; then
	echo "Looking for user dir name..."
	sleep 1  	# sometimes adb complains: device not found
	# look for dirname which looks like md5 (32 alpha-numeric chars)
	userList=$(adb ls $RES_DIR | cut -f 4 -d ' ' | sed 's/[^0-9a-z]//g' \
		| awk '{if (length() == 32) print}')
	numUser=$(echo "$userList" | wc -l)
	# choose the first user.
	chooseUser=$(echo "$userList" | head -n1)
	[[ -n $chooseUser ]] || {
		>&2 echo "Could not find user. Please check whether your resource dir is $RES_DIR"
		exit 1
	}
	echo "Found $numUser user(s). User chosen: $chooseUser"

	if [[ $1 == "res" ]]; then
		mkdir -p resource; cd resource
		echo "Pulling resources... "
		for d in avatar image2 voice2 emoji video sfs; do
			adb shell "cd $RES_DIR/$chooseUser &&
								 tar czf - $d 2>/dev/null | base64" |
					base64 -di | tar xzf -

			# Old Slow Way:
			# mkdir -p $d; cd $d
			# adb pull "$RES_DIR/$chooseUser/$d"
			# cd ..
			[[ -d $d ]] || {
				>&2 echo "Failed to download resource directory: $RES_DIR/$chooseUser/$d"
				exit 1
			}
		done
		cd ..
		echo "Resource pulled at ./resource"
		echo "Total size: $(du -sh resource | cut -f1)"
	else
		echo "Pulling database and avatar index file..."
		adb pull $MM_DIR/MicroMsg/$chooseUser/EnMicroMsg.db
		[[ -f EnMicroMsg.db ]] && \
			echo "Database successfully downloaded to EnMicroMsg.db" || {
			>&2 echo "Failed to pull database by adb"
			exit 1
		}
		adb pull $MM_DIR/MicroMsg/$chooseUser/sfs/avatar.index
		[[ -f avatar.index ]] && \
			echo "Avatar index successfully downloaded to avatar.index" || {
				>&2 echo "Failed to pull avatar index by adb, are you using latest version of wechat?"
				exit 1
			}
	fi
else
	echo "Usage: $0 <res|db>"
	exit 1
fi

