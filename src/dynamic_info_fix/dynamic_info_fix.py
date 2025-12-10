import random
import pandas as pd
import json
import re

from common import preprocess_punc, value_type_verify, unit_type_verify, host_type_verify, path_type_verify, pattern_to_regex, ip_format_verify, path_format_verify
from dynamic_format_generation.format_memory import ValidatedFormat, RejectedFormat, RejectOutput
from dynamic_format_generation.format_extract import FormatExtractor

dynamic_types = ['Unit', 'Value', 'Identifier', 'Path', 'Undecided']

def get_dynamic_based_info(sampled_representative_info):
    dynamic_representative_info = []
    n_para = len(sampled_representative_info[0])
    p_index = 0
    while p_index < n_para:
        para_list = []
        for para_info in sampled_representative_info:
            if para_info[p_index] in para_list:
                pass
            else:
                para_list.append(para_info[p_index])
        dynamic_representative_info.append(para_list)
        p_index += 1
    return dynamic_representative_info

def dynamic_based_df_generate(new_structured_df, templates, extract_from_file):
    dynamic_based_df_list = []
    for template in templates:
        selected_df = new_structured_df[new_structured_df['NewTemplate'] == template]
        selected_unique_df = selected_df.drop_duplicates(subset='Content', keep='first')
        ori_template = selected_df['EventTemplate'].iloc[0]

        para_info_list = selected_unique_df['ParameterList'].tolist()
        dynamic_based_info = get_dynamic_based_info(para_info_list)
        content_list = selected_unique_df['Content'].tolist()

        para_index = 0
        while para_index < len(dynamic_based_info):
            para_value_list = dynamic_based_info[para_index]
            dynamic_based_df_list.append([ori_template, template, content_list, para_index, para_value_list])
            para_index += 1

    headers = ['Template', 'NewTemplate', 'ContentList', 'ParameterIndex', 'ParameterValue']
    dynamic_based_df = pd.DataFrame(dynamic_based_df_list, columns=headers)
    return dynamic_based_df

def representative_df_extract(new_structured_df, templates, n_representative, extract_from_file):
    representative_df_list = []
    for template in templates:
        selected_df = new_structured_df[new_structured_df['NewTemplate'] == template]
        selected_unique_df = selected_df.drop_duplicates(subset='Content', keep='first')
        ori_template = selected_df['EventTemplate'].iloc[0]

        dynamic_representative_info = []
        content_list = []
        if len(selected_unique_df) < n_representative:
            sampled_df = selected_unique_df.sample(n=len(selected_unique_df), random_state=19970411)
            para_info_list = sampled_df['ParameterList'].tolist()
            dynamic_representative_info = get_dynamic_based_info(para_info_list)
            content_list = sampled_df['Content'].tolist()
        else:
            sampled_df = selected_unique_df.sample(n=n_representative, random_state=19970411)
            para_info_list = sampled_df['ParameterList'].tolist()
            dynamic_representative_info = get_dynamic_based_info(para_info_list)
            content_list = sampled_df['Content'].tolist()

        """The following is construct the structure of new dataframe for dynamic information fix"""
        para_index = 0
        while para_index < len(dynamic_representative_info):
            para_value_list = dynamic_representative_info[para_index]
            representative_df_list.append([ori_template, template, content_list, para_index, para_value_list])
            para_index += 1

    headers = ['Template', 'NewTemplate', 'ContentList', 'ParameterIndex', 'ParameterValue']
    representative_df = pd.DataFrame(representative_df_list, columns=headers)
    return representative_df

def preprocess(dynamic_based_df, temp_index_dict):
    dynamic_based_updated_df_list = []
    for row in dynamic_based_df.itertuples(index=False):
        para_values = row.ParameterValue
        content_list = row.ContentList[0]
        template = row.NewTemplate
        para_index = row.ParameterIndex
        """Preprocess parameter"""
        if value_type_verify(para_values):
            token_format = '<D>'
            value_type = 'Value'
            para_list = para_values
            dynamic_based_updated_df_list.append(
                [template, content_list, para_index, para_values, token_format, para_list, value_type])
        else:
            token_format, para_list = preprocess_punc(para_values)
            value_type = 'Undecided'
            if value_type_verify(para_list):
                value_type = 'Value'
                dynamic_based_updated_df_list.append(
                    [template, content_list, para_index, para_values, token_format, para_list, value_type])
            elif unit_type_verify(para_list):
                value_type = 'Unit'
                dynamic_based_updated_df_list.append(
                    [template, content_list, para_index, para_values, token_format, para_list, value_type])
            elif host_type_verify(para_list):
                value_type = 'Identifier'
                token_format = token_format.replace('<D>', '<D>:<D>')
                dynamic_based_updated_df_list.append(
                    [template, content_list, para_index, para_values, token_format, para_list, value_type])
            elif path_type_verify(para_list):
                value_type = 'Path'
                dynamic_based_updated_df_list.append(
                    [template, content_list, para_index, para_values, token_format, para_list, value_type])
            else:
                dynamic_based_updated_df_list.append(
                    [template, content_list, para_index, para_values, token_format, para_list, value_type])
    headers = ['Template', 'ContentList', 'ParameterIndex', 'Tokens', 'TokenFormat', 'ValueList', 'ValueType']
    dynamic_based_updated_df = pd.DataFrame(dynamic_based_updated_df_list, columns=headers)
    return dynamic_based_updated_df

"""TODO: connect value with its corresponding unit, generated a new dataframe"""
def combine_value_unit(structured_df, dynamic_based_df):
    pass

"""TODO: generate token format and extract value with LLM"""
def pattern0_match_pattern1(tmp0, tmp1):
    regex0 = pattern_to_regex(tmp0)
    match = re.search(regex0, tmp1)
    if (match):
        return True
    else:
        return False

def insert_pattern(tmp, tmplist):
    index = 0
    for t in tmplist:
        if ((pattern0_match_pattern1(t, tmp) == True) and (pattern0_match_pattern1(tmp, t) == False)):
            return index
        else:
            index = index + 1
    return -1

def fix_fault_format(pattern_list):
    new_pattern_list = []
    for pattern in pattern_list:
        fixed_pattern = pattern
        fixed_pattern = re.sub(r'(?:<D>\s*){2,}', '<D>', fixed_pattern)
        new_pattern_list.append(fixed_pattern)
    return new_pattern_list

def refine_pattern_list(pattern_list):
    pattern_list = fix_fault_format(pattern_list)
    new_pattern_list = []
    for index in range(0, len(pattern_list)):
        if (pattern_list[index] in new_pattern_list):
            pass
        else:
            pos = insert_pattern(pattern_list[index], new_pattern_list)
            if (pos == -1):
                new_pattern_list.append(pattern_list[index])
            else:
                new_pattern_list.insert(pos, pattern_list[index])
    return new_pattern_list

def get_unmatched_value(value_list, matched_value_list):
    unmatched_value_list = []
    for value in value_list:
        if value in matched_value_list:
            pass
        else:
            unmatched_value_list.append(value)
    return unmatched_value_list

def output_validate(llm_output):
    try:
        return json.loads(llm_output)
    except json.JSONDecodeError:
        return None

def match_value_with_format(value_list, format_list):
    format_value_dict = {}
    format_seperate_value_dict = {}
    unmatched_value_list = value_list[:]
    unmatched_format_list = []
    format_list = refine_pattern_list(format_list)
    for format in format_list:
        format_value_dict[format] = []
        format_seperate_value_dict[format] = []
        format_regex = pattern_to_regex(format)
        matched_value_list = []
        for value in unmatched_value_list:
            if re.match(format_regex, value):
                matched_value_list.append(value)
                format_value_dict[format].append(value)
                para_list = re.findall(format_regex, value)[0]
                if isinstance(para_list, tuple):
                    para_list = list(para_list)
                    format_seperate_value_dict[format].append(para_list)
                else:
                    para_list = [para_list]
                    format_seperate_value_dict[format].append(para_list)
        if len(format_value_dict[format]) == 0:
            unmatched_format_list.append(format)
        unmatched_value_list = [v for v in unmatched_value_list if v not in matched_value_list]
    return unmatched_format_list, unmatched_value_list, format_value_dict, format_seperate_value_dict

def fix_format(format_seperate_value_dict, format_value_dict):
    keys = list(format_value_dict.keys())
    for format in keys:
        if ip_format_verify(format) or path_format_verify(format):
            vals_from_value = format_value_dict.pop(format, [])
            vals_from_separate = format_seperate_value_dict.pop(format, [])

            format_value_dict.setdefault('<D>', [])
            format_seperate_value_dict.setdefault('<D>', [])

            format_value_dict['<D>'].extend(vals_from_value)
            format_seperate_value_dict['<D>'].extend(vals_from_value)
    return format_seperate_value_dict, format_value_dict

def llm_generated_format_repair(format_list):
    new_format_list = []
    for format in format_list:
        new_format = format
        new_format = re.sub(r'<D(?!>)', '<D>', new_format)
        new_format = re.sub(r'(?<!<)D>', '<D>', new_format)
        new_format_list.append(new_format)
    return new_format_list

def value_format_generate(dynamic_based_updated_df, sample_ratio = 0.25, min_size = 5):
    validated_format_memory = ValidatedFormat()
    rejected_format_memory = RejectedFormat()
    rejected_output_memory = RejectOutput()
    format_extactor = FormatExtractor(validated_format_memory, rejected_format_memory, rejected_output_memory)
    dynamic_format_df_info = []
    index = 0
    num = len(dynamic_based_updated_df)

    for row in dynamic_based_updated_df.itertuples(index=False):
        print((index/num)*100)
        index=index+1
        if row.ValueType == 'Undecided':
            value_list = row.ValueList
            print(value_list)
            sampled_list = []
            sample_size = int(len(value_list) * sample_ratio)
            if sample_size < min_size:
                if len(value_list) < min_size:
                    sampled_list = value_list
                else:
                    sampled_list = random.sample(value_list, min_size)
            else:
                sampled_list = random.sample(value_list, sample_size)
            llm_output = format_extactor.extract(sampled_list, use_retry=1)
            print(llm_output)
            format_list = output_validate(llm_output)
            while (format_list == None):
                rejected_output_memory.add_output(llm_output)
                llm_output = format_extactor.extract(sampled_list, use_retry=2)
                print(llm_output)
                format_list = output_validate(llm_output)
            rejected_output_memory.clean_outputs()
            format_list = llm_generated_format_repair(format_list)
            unmatched_format_list, unmatched_value_list, format_value_dict, format_seperate_value_dict = match_value_with_format(
                value_list, format_list)
            for format in unmatched_format_list:
                rejected_format_memory.add_format(format)
            while (len(unmatched_value_list) > 0):
                llm_output = format_extactor.extract(unmatched_value_list, use_retry=0)
                print(llm_output)
                format_list = output_validate(llm_output)
                while (format_list == None):
                    rejected_output_memory.add_output(llm_output)
                    llm_output = format_extactor.extract(sampled_list, use_retry=2)
                    print(llm_output)
                    format_list = output_validate(llm_output)
                format_list = llm_generated_format_repair(format_list)
                unmatched_format_list, unmatched_value_list, format_value_dict_tmp, format_seperate_value_dict_tmp = match_value_with_format(
                    unmatched_value_list, format_list)
                for format in unmatched_format_list:
                    rejected_format_memory.add_format(format)
                format_value_dict.update(format_value_dict_tmp)
                format_seperate_value_dict.update(format_seperate_value_dict_tmp)
            format_seperate_value_dict = {k: v for k, v in format_seperate_value_dict.items() if v}
            format_value_dict = {k: v for k, v in format_value_dict.items() if v}
            format_seperate_value_dict, format_value_dict = fix_format(format_seperate_value_dict, format_value_dict)
            for format in format_seperate_value_dict.keys():
                seperated_value_list = format_seperate_value_dict[format]
                value_list = format_value_dict[format]
                token_format = row.TokenFormat
                token_list = [token_format.replace('<D>', value) for value in value_list]
                token_format = token_format.replace('<D>', format)
                new_row = [row.Template, row.ParameterIndex, token_format, token_list, seperated_value_list, row.ValueType]
                dynamic_format_df_info.append(new_row)
        else:
            new_row = [row.Template, row.ParameterIndex, row.TokenFormat, row.Tokens, row.ValueList, row.ValueType]
            dynamic_format_df_info.append(new_row)

    headers = ['Template', 'ParameterIndex', 'TokenFormat', 'Tokens', 'ValueList', 'ValueType']
    dynamic_format_df = pd.DataFrame(dynamic_format_df_info, columns=headers)
    return dynamic_format_df