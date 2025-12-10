parser=Spell
output_dir=../../Output/sample_files

for dataset in Hadoop
do
  python sample_file_extract.py --d ${dataset} --p ${parser} --o ${output_dir}
done