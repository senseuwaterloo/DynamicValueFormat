import pandas as pd
import difflib

from utils.common import common_args

def exact_cluster_mapping(df1, df2, line_col='LineId', cluster_col='EventTemplate'):
    # group -> set
    g1 = df1.groupby(cluster_col)[line_col].apply(set).to_dict()
    g2 = df2.groupby(cluster_col)[line_col].apply(set).to_dict()

    # invert g2 by frozenset -> list of cluster ids (防止不同cluster但成员完全相同)
    inv_g2 = {}
    for cid2, s2 in g2.items():
        inv_g2.setdefault(frozenset(s2), []).append(cid2)

    # 找精确匹配
    matches = []
    for cid1, s1 in g1.items():
        matched = inv_g2.get(frozenset(s1), [])
        for cid2 in matched:
            matches.append({'PDrain_template': cid1, 'EventTemplate': cid2})

    return pd.DataFrame(matches)

def similarity(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()

if __name__ == "__main__":
    args = common_args()
    dataset = args.dataset
    parser_name = args.parser
    output_dir = args.output
    n_sample = args.sample

    base_file = '../../data/Drain_result/' + dataset + '_full.log_structured.csv'
    structured_file = '../../data/' + parser_name + '_result/' + dataset + '_full.log_structured.csv'

    # base_file_template = '../../data/Drain_result/' + dataset + '_full.log_templates.csv'
    # template_file = '../../data/' + parser_name + '_result/' + dataset + '_full.log_templates.csv'

    base_df = pd.read_csv(base_file)
    structured_df = pd.read_csv(structured_file)

    template_df = exact_cluster_mapping(base_df, structured_df)
    template_pairs = list(template_df[['PDrain_template', 'EventTemplate']].itertuples(index=False, name=None))
    template_pairs_sorted = sorted(template_pairs, key=lambda x: similarity(x[0], x[1]))
    for pair in template_pairs_sorted:
        print(pair, similarity(pair[0], pair[1]))