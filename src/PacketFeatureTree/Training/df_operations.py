def split_by_proto(TEST_PROTO, FULL_DF):
    train, test = FULL_DF[FULL_DF['Protocol']!=TEST_PROTO], FULL_DF[FULL_DF['Protocol']==TEST_PROTO]
    condition = sorted(train['Class'].unique())==sorted(test['Class'].unique())
    #print(condition, type(condition))
    assert [condition], f"{sorted(FULL_DF[train]['Class'].unique())=} {sorted(FULL_DF[test]['Class'].unique())=}"
    return train, test

def split_by_many_proto(TEST_PROTOS, df):
    assert type(TEST_PROTOS) is list
    train_idx, test_idx = df['Protocol'].isin(TEST_PROTOS), ~df['Protocol'].isin(TEST_PROTOS)
    assert sorted(df[train_idx]['Class'].unique()) == sorted(df[test_idx]['Class'].unique()), f"{sorted(df[train_idx]['Class'].unique())=} {sorted(df[test_idx]['Class'].unique())=}"
    return train_idx, test_idx


def get_train_cv(df):
    remaining_protocols = list(set([x[1] for x in df[['Class','Protocol']].value_counts().sort_index().index.to_numpy()]))
    for i in range(2):
        yield split_by_many_proto(remaining_protocols[i::2], df)

def remove_unique_rows(df, columns):
    # Group the DataFrame by the specified columns
    grouped = df.groupby(columns)
    # Filter the groups that have more than one row
    df_filtered = grouped.filter(lambda x: x.shape[0] > 1)
    return df_filtered

def distribute_items(df):
    # Thanks ChatGPT
    # Create a dictionary that maps each item to its associated class(es)
    item_classes = {}
    for index, row in df.iterrows():
        item = row['Protocol']
        item_class = row['Class']
        
        if item not in item_classes:
            item_classes[item] = set()
        
        item_classes[item].add(item_class)
    
    # Create two empty lists to hold the items in each group
    group1 = []
    group2 = []
    
    # Keep track of the classes covered by each group
    classes_covered_by_group1 = set()
    classes_covered_by_group2 = set()
    
    # Iterate over the items and divide them into two groups
    for item in item_classes.keys():
        # Check which group has fewer classes covered and add the item to that group
        if len(classes_covered_by_group1.intersection(item_classes[item])) <= len(classes_covered_by_group2.intersection(item_classes[item])):
            group1.append(item)
            classes_covered_by_group1.update(item_classes[item])
        else:
            group2.append(item)
            classes_covered_by_group2.update(item_classes[item])
    
    return group1, group2