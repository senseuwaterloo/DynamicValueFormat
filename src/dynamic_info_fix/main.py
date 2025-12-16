import pandas as pd
import time

from dynamic_info_combine import generate_combined_dynamic_template, generate_combined_dynamic_structured_df, get_template_with_dynamic
from dynamic_info_fix import dynamic_based_df_generate, preprocess, value_format_generate, dynamic_based_df_generate_v2

if __name__ == "__main__":
    structured_file = '../../data/Drain_result/Apache_full.log_structured.csv'
    template_file = '../../data/Drain_result/Apache_full.log_templates.csv'

    # output_file_structured = '../../Output/dynamic_extract/structured_file/Spark_dynamic_structured.csv'
    # output_file_preprocessed = '../../Output/dynamic_extract/preprocessed/Spark_dynamic_preprocessed.csv'
    output_file_format = '../../Output/dynamic_extract/format/Apache_dynamic_format.csv'

    begin = time.time()

    template_df = pd.read_csv(template_file)
    structured_df = pd.read_csv(structured_file)

    template_list = template_df['EventTemplate'].tolist()
    new_old_template_dict, template_dynamic_dict= generate_combined_dynamic_template(template_list)
    new_structured_df, new_old_template_dict, template_dynamic_dict = generate_combined_dynamic_structured_df(structured_df, new_old_template_dict, template_dynamic_dict)
    template_with_dynamic = get_template_with_dynamic(template_list)
    print('Finish original data fix')
    data_fix = time.time()
    print(data_fix - begin)
    # new_structured_df.to_csv(output_file_structured, index=False)

    """Use new template as index in the following part"""
    new_template_list_with_dynamic = []
    for template in template_with_dynamic:
        new_template = new_old_template_dict[template]
        new_template_list_with_dynamic.append(new_template)
    dynamic_based_df = dynamic_based_df_generate_v2(new_structured_df, new_template_list_with_dynamic, extract_from_file=False)
    print('Finish dynamic based data generation')
    dynamic_based = time.time()
    print(dynamic_based - begin)

    dynamic_based_updated_df = preprocess(dynamic_based_df, template_dynamic_dict)
    print('Finish dynamic based data preprocess')
    preprocess = time.time()
    print(preprocess - begin)
    # dynamic_based_updated_df[['Template', 'ParameterIndex', 'Tokens', 'TokenFormat', 'ValueList', 'ValueType']].to_csv(output_file_preprocessed, index=False)

    """Generate dynamic variable format for undecided type value"""
    print('Begin dynamic format extraction')
    dynamic_format_df = value_format_generate(dynamic_based_updated_df)
    dynamic_format_df.to_csv(output_file_format)