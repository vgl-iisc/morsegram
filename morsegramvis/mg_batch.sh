
# run the command
# command = "python3 main.py --mode auto  /home/rathoddinesh/Bit\ Repos/morsegram/Chess/under_segmentations/1089507.raw"

cd /home/rathoddinesh/Bit\ Repos/morsegram/python\ routines/

# iterate over all the files in the directory
for file in /home/rathoddinesh/Bit\ Repos/morsegram/Chess/under_segmentations/*.raw
do
    echo "Processing $file file..."

    # run the command for each file( file contrains space so we need to use quotes)
    python3 main.py --mode auto "$file"

    cd ../

    # get location of last slash
    last_slash=$(echo $file | awk -F/ '{print NF}')

    # get the file name after the last slash
    file_name=$(echo $file | cut -d'/' -f$last_slash)

    # remove the .raw extension
    file_name=$(echo $file_name | cut -d'.' -f1)

    # create a folder with the file name
    mkdir $file_name

    # move folder to file_name folder
    mv Outputs $file_name
    cd python\ routines/

    mv *.svg ../$file_name

done

echo "Running the command"