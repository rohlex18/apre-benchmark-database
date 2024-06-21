from sklearn.datasets import make_classification
from sklearn.calibration import CalibratedClassifierCV
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, VotingClassifier
from sklearn.linear_model import SGDClassifier, LogisticRegressionCV
from imblearn.over_sampling import RandomOverSampler
from sklearn.base import clone
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import ConfusionMatrixDisplay, log_loss
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pickle

from .df_operations import split_by_many_proto, split_by_proto, distribute_items

def build_byte_models(TrainDF):

    cs = np.array(['ABSOLUTE_TIME', 'ETHER', 'IPv4', 'UINT16', 'UINT32',
        'UINT8', 'STRING'], dtype=object)

    res = {'Protocol': [],
        'Logistic Regression': [],
        'Gradient Boosting': [],
        'Random Forest': [],
        'Stochastic Gradient Descent': []}
        

    for proto in TrainDF['Protocol'].unique():
        print('\t',proto)
        train, test = split_by_proto(proto, TrainDF)
        my_train = train.drop_duplicates(subset=train.columns[:16].tolist() + ['Class'] + ['Protocol'])
        X = my_train.iloc[:, :16]
        y = my_train['Class']
        train_protos, test_protos = distribute_items(my_train[['Class','Protocol']].value_counts().to_frame('counts').reset_index(level=[0,1]))
        
        train_idx, val_idx = split_by_many_proto(train_protos, my_train)

        X_train, y_train = X[train_idx], y[train_idx]
        #X_train, y = ros.fit_resample(X, y)
        X_cal, X_val, y_cal, y_val = train_test_split(X[val_idx], y[val_idx], test_size=0.5, random_state=42)

        X_test = test.iloc[:, :16]
        y_test = test['Class']
        
        
        uniform_proba = np.ones((len(X_val), len(cs)))/len(cs)
        uloss = log_loss(y_val, uniform_proba, labels = cs)
        print('uniform loss', uloss)
        
        res_proto = [proto]#, uloss]
        
        clfs = [LogisticRegressionCV(random_state=1337, class_weight='balanced', solver='newton-cg'),
                GradientBoostingClassifier(loss='log_loss', max_depth = 8, random_state = 1337),
                RandomForestClassifier(criterion='log_loss', random_state=1337, class_weight='balanced'),
                SGDClassifier(loss='log_loss', random_state=1337, class_weight='balanced')]
        
        gbc_parameters = {'n_estimators': [5,10],
                                'subsample': [0.5,1],
                                'criterion': ['friedman_mse', 'squared_error'],
                                'max_depth': [3,8]
                                }
        
        rfc_parameters = {'n_estimators': [10,100],
                                'criterion': ['log_loss'],
                                'max_depth': [3, None],
                                'min_samples_leaf' : [1,5,10],
                                'max_features': ['sqrt','log2', None]
                                }
        
        sgd_parameters = {'penalty': ['l2', 'l1', 'elasticnet', None],
                                'loss': ['log_loss'],
                                'alpha': [0.0001,0.001,0.01],
                                'max_iter' : [100,1000,10000]
                                }
        
        params = ['', gbc_parameters, rfc_parameters, sgd_parameters]
        #clfs.append(VotingClassifier(estimators=[(k,clf) for k, clf in zip(['sgd','rfc', 'gbc'], clfs)], voting='soft'))
        final_models = []
        for base_clf, parameters in zip(clfs, params):

            print('--->', base_clf)
            clone(base_clf) #ensure no dirty classifiers
            
    

            base_clf.fit(X_train, y_train)

            for method in ['sigmoid']:

                calibrated_clf = CalibratedClassifierCV(base_clf, cv='prefit', method=method)
                calibrated_clf.fit(X_cal, y_cal)

                #assert (calibrated_clf.classes_ == cs).all()

                clf_loss = log_loss(y_val, calibrated_clf.predict_proba(X_val), labels = cs)
                print(f'{method=}, {clf_loss=}')
                #print(GSVC.best_params_) 
                final_models.append(calibrated_clf)
                res_proto.append(clf_loss)
        
        best_model_index = np.argmin(np.array(res_proto[-4:]))
        print('best', list(res.keys())[1+best_model_index], res_proto[-4:][best_model_index])
        best_clf = final_models[best_model_index]
        
        with open(f'../ByteLabelModels/clf_{proto}.pkl', 'wb') as file:
            pickle.dump(best_clf, file)
            
        with open(f'../ByteLabelModels/clf_{proto}_base.pkl', 'wb') as file:
            pickle.dump(clfs[best_model_index], file)

        ConfusionMatrixDisplay.from_estimator(best_clf, X_test, y_test)
        plt.xticks(rotation='vertical')
        plt.show()

                    
        res_proto.append(clf_loss)
                    
    
        for k,v in zip(res.keys(), res_proto):
            res[k] = res[k] + [v]
        
    df = pd.DataFrame.from_dict(res)
    return df

def full_save(name):
    plt.tight_layout()
    plt.savefig(f'{name}.pdf', bbox_inches='tight',pad_inches = 0)
    #plt.savefig(f'../LitReviewPlots/{name}/{name}.pgf')
    plt.show()
    return None

import matplotlib as mpl

def plot_cali(cs, probas, y_test, ax, marker='.', alpha=1):
    default_colors = mpl.rcParams['axes.prop_cycle'].by_key()['color']

    for i, class_ in enumerate(cs):
        bin_classes = [y_test==class_][0].values
        if bin_classes.sum()>0:
            prob_true, prob_pred = calibration_curve(bin_classes, probas[:,i], n_bins=10, strategy='quantile')
            ax.plot(prob_pred, prob_true, label=class_, marker=marker, c=default_colors[i], alpha=alpha)

    ax.plot(np.linspace(0,1,10),np.linspace(0,1,10),c='black',linestyle='dashed')
    ax.set_xlabel('Predicted Probability', size=28)
    return log_loss(y_test, probas, labels = cs)

    

import joblib
from sklearn.calibration import calibration_curve

def create_cali_plots(protocol, TrainDF):
    model = joblib.load( f'ByteLabelModels/clf_{protocol}.pkl')
    base = joblib.load( f'ByteLabelModels/clf_{protocol}_base.pkl')
    train, test = split_by_proto(protocol, TrainDF)
    my_train = train.drop_duplicates(subset=train.columns[:16].tolist() + ['Class'] + ['Protocol'])
    X = my_train.iloc[:, :16]
    y = my_train['Class']
    remaining_protocols = my_train[['Class','Protocol']].value_counts().sort_index().index.get_level_values(1).unique().tolist()
    train_idx, val_idx = split_by_many_proto(remaining_protocols[::2], my_train)
    X_train, y_train = X[train_idx], y[train_idx]
    X_cal, X_val, y_cal, y_val = train_test_split(X[val_idx], y[val_idx], test_size=0.5, random_state=42)
    
    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(16,8), sharey = True)
    axes = axes.flatten()
    l_base = plot_cali(cs, base.predict_proba(X_val), y_val, axes[0])
    l_cali = plot_cali(cs, model.predict_proba(X_val), y_val, axes[1])
    axes[0].set_ylabel('True Probability', size=28)
    axes[0].set_title(f'Base Model (Log Loss {round(l_base, 2)})', size=36)
    axes[1].set_title(f'Calibrated Model (Log Loss {round(l_cali, 2)})', size=36)
    plt.legend( prop={'size': 16},  ncol=2)
    full_save('Plotting/{protocol}/{protocol}_Cali_Plot/{protocol}_Cali_Plot_temp')
    
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(8,8))
    plot_cali(cs, base.predict_proba(X_val), y_val, ax)
    ax.set_ylabel('True Probability', size=28)
    full_save('Plotting/{protocol}/{protocol}_Cali_Plot/base_model')
    
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(8,8))
    plot_cali(cs, model.predict_proba(X_val), y_val, ax)
    ax.set_ylabel('True Probability', size=28)
    full_save('Plotting/{protocol}/{protocol}_Cali_Plot/cali_model')