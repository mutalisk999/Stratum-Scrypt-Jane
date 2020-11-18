ps -ef |grep twistd |grep -v grep |awk '{print $2}'|xargs kill -9
