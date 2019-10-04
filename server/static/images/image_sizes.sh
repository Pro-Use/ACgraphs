list=( $(ls | grep B) ) 

for i in "${list[@]}"; do 
	identify -format "%f %G\n" $i
	width=$(identify -format "%w" $i)
	height=$(identify -format "%h" $i)
	devided=$(($width / 16))
	ratio=$(($devided * $height))
	echo 16:$ratio
done
