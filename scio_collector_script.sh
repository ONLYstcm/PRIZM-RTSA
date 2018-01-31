pi_dataLocationPol0='/home/pi/data_100MHz'
pi_dataLocationPol1='/home/pi/data_70MHz'
destinationLocation=$(pwd)
filePol0='pol0.scio'
filePol1='pol1.scio'
key=""
i=1

echo "PLEASE MAKE SURE YOU ESTABLISHED A SSH_RSA KEY PAIR ON THE RASPBERRY PI"
echo "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
echo "Enter IP address of RaspberryPi:"
read ipAddress
echo "Attempting to connect to RaspberryPi at pi@$ipAddress"
echo "========================================================="
sleep 1

while [ true ]; do	# Loop indefinitely out of the loop

parentDIRPol0=$(ssh pi@$ipAddress ls $pi_dataLocationPol0/ | tail -2| head -1)	#e.g Get this part '15030' in directory ~/data_100MHz/15030/1503004514
childDIRPol0=$(ssh pi@$ipAddress ls $pi_dataLocationPol0/$parentDIRPol0/ | tail -1) #e.g Get this part '1503004514' in directory ~/data_100MHz/15030/1503004514
parentDIRPol1=$(ssh pi@$ipAddress ls $pi_dataLocationPol1/ | tail -2| head -1)	#e.g Get this part '15030' in directory ~/data_70MHz/15030/1503004514
childDIRPol1=$(ssh pi@$ipAddress ls $pi_dataLocationPol1/$parentDIRPol1/ | tail -1) #e.g Get this part '1503004514' in directory ~/data_70MHz/15030/1503004514


echo "Connected to RaspberryPi at pi@$ipAddress"
echo "============================================="
sleep 1
echo "Getting data from directory pi@$ipAddress:$pi_dataLocationPol0/$parentDIRPol0/$childDIRPol0/"
echo "Getting data from directory pi@$ipAddress:$pi_dataLocationPol1/$parentDIRPol1/$childDIRPol1/"

sleep 3

rm $filePol0.bz2
rm $filePol1.bz2

     until $(test -s "$destinationLocation/$filePol0.bz2"); do #Repeat until the non-zero compressed file appears in the copy destination indicating SNAP board has 							   #completed its cycle and is creating a new directory


	#Check if the file on the RaspberryPi has updated in size therefore indicating new data or if bz2 file is found on RaspberryPi
	#Pol 0
	if  	!($(cmp -s pi@$ipAddress:$pi_dataLocationPol0/$parentDIRPol0/$childDIRPol0/$filePol0 $destinationLocation/$filePol0)) \
		|| $(ssh pi@$ipAddress test -s "$pi_dataLocationPol0/$parentDIRPol0/$childDIRPol0/$filePol0.bz2"); then #(test "$filePol0_size_pi">"$filePol0_size_local")

		scp pi@$ipAddress:$pi_dataLocationPol0/$parentDIRPol0/$childDIRPol0/$filePol0.bz2 $destinationLocation/  && bzip2 -dkf 	$destinationLocation/$filePol0.bz2 \
		|| scp pi@$ipAddress:$pi_dataLocationPol0/$parentDIRPol0/$childDIRPol0/$filePol0 $destinationLocation #Try SSH copy of the bz2 file, Catch SSH copy of the scio file

	fi
	#Pol 1
	if  	!($(cmp -s pi@$ipAddress:$pi_dataLocationPol1/$parentDIRPol1/$childDIRPol1/$filePol1 $destinationLocation/$filePol1)) \
		|| $(ssh pi@$ipAddress test -s "$pi_dataLocationPol1/$parentDIRPol1/$childDIRPol1/$filePol1.bz2"); then #(test "$filePol1_size_pi">"$filePol1_size_local")

		scp pi@$ipAddress:$pi_dataLocationPol1/$parentDIRPol1/$childDIRPol1/$filePol1.bz2 $destinationLocation/  && bzip2 -dkf 	$destinationLocation/$filePol1.bz2 \
		|| scp pi@$ipAddress:$pi_dataLocationPol1/$parentDIRPol1/$childDIRPol1/$filePol1 $destinationLocation #Try SSH copy of the bz2 file, Catch SSH copy of the scio file

	fi

	sleep 1

	done

done

echo " "
echo "------------------------------------------------------"
echo "PRIZM data capturing at 100MHz and 70MHz interrupted"

exit
