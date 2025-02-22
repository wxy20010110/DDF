"""
System Environment
OS: Windows 10 家庭中文版
CPU: intel(R) Core(TM) i7-7700HQ CPU @ 2.80GHz 2.80GHz
GPU: GeForce GTX 1050
CUDA 9.1.84
Memory: 16 GiB

Python Environment
python 3.7.4 (anaconda)
numpy 1.16.5 
pandas 0.25.1
pytorch 1.1.0
scikit-learn 0.21.3
scipy 1.3.1
matplotlib 3.1.1
"""

'''
分析中常用的工具与数据
'''
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import recall_score
from sklearn.metrics import precision_score
from sklearn.metrics import accuracy_score
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import KFold
from sklearn.tree import plot_tree
from scipy.spatial.distance import pdist, cdist
from scipy.spatial.distance import squareform
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.gaussian_process.kernels import RBF
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis

X = np.load("./processedData/X/X_train.npy")
x = np.load("./processedData/X/x_test.npy")
Y = np.load("./processedData/Y/Y_train.npy")
y = np.load("./processedData/Y/y_test.npy")

reactantCombination = np.load(
    "./processedData/X/reactComb.npy", allow_pickle=True)


reactComb = np.load(
    "./processedData/X/reactComb.npy", allow_pickle=True)

reactantMask = ["XXXinorg1", "XXXinorg2", "XXXinorg3", "XXXorg1", "XXXorg2"]

'''
转化分类结果。结果有1，2，3，4。但是3，4对应人的预测1，1,2对应预测0
'''


def numout2boolout(label):
    return label > 2.5


'''
作者使用的SVM核, 使用了https://github.com/rlphilli/sklearn-PUK-kernel的代码
'''


def PUK_kernel(X1, X2, sigma=1.0, omega=1.0):
    if X1 is X2:
        kernel = squareform(pdist(X1, 'sqeuclidean'))
    else:
        kernel = cdist(X1, X2, 'sqeuclidean')
    kernel = (1 + (kernel * 4 * np.sqrt(2**(1.0/omega)-1)) / sigma**2) ** omega
    kernel = 1/kernel
    return kernel


'''
作者使用的交叉验证方法： 注意同一反应物组合的反应要划分在同一训练集或验证集。
Model是使用的模型的名称或构造函数，params为传入的参数。
shuffle表示是否对数据重新排列
scale表示是否对数据进行标准化
'''
def CV_author(X, Y, n_splits, Model, params, scale=True, shuffle=True):
    if scale:
        X = StandardScaler().fit_transform(X)  # 标准化数据
    kf = KFold(n_splits=n_splits, shuffle=shuffle)  # 随机划分训练集与测试集中的反应组合

    for train_index_rc, test_index_rc in kf.split(reactantCombination):
        train_index = [
            i for rc in train_index_rc for i in reactantCombination[rc]]
        test_index = [
            i for rc in test_index_rc for i in reactantCombination[rc]]
        X_train, X_test = X[train_index], X[test_index]
        Y_train, Y_test = Y[train_index], Y[test_index]
        model = Model(**params)
        model.fit(X_train, Y_train)
        pred = model.predict(X_test)
        Y_test = numout2boolout(Y_test)
        pred = numout2boolout(pred)
        print("recall={:.3f}".format(
            recall_score(Y_test, pred, average='weighted')))
        print("precision={:.3f}".format(
            precision_score(Y_test, pred, average="weighted")))
        print("accuracy={:.3f}".format(accuracy_score(Y_test, pred)))
        print("confusion matrix is")
        print(confusion_matrix(Y_test, pred))


'''
在测试集上验证。对数据进行标准化
'''
def test(X, Y, x, y, Model, params, scale=True):
    if scale:
        scaler = StandardScaler()
        X = scaler.fit_transform(X)  # 标准化数据
        x = scaler.transform(x)

    model = Model(**params)
    model.fit(X, Y)
    pred = model.predict(x)
    boolpred = numout2boolout(pred)
    booly = numout2boolout(y)

    print("recall={:.3f}".format(
        recall_score(booly, boolpred, average='weighted')))
    print("precision={:.3f}".format(
        precision_score(booly, boolpred, average="weighted")))
    print("accuracy={:.3f}".format(accuracy_score(booly, boolpred)))
    print("confusion matrix is")
    print(confusion_matrix(booly, boolpred))
    return pred,model.predict(X)

'''
将模型重解释为决策树
'''
def reinterpret(X_model,model,X_tree):
    pred=model.predict(X_model)
    ret=DecisionTreeClassifier()
    ret.fit(X_tree,pred)
    return ret

'''
作出学习曲线
'''

def learning_curve(X, Y, Model, params, pace, n_splits, scale=True):
    if scale:
        X = StandardScaler().fit_transform(X)  # 标准化数据
    kf = KFold(n_splits=n_splits, shuffle=True)  # 随机划分训练集与测试集中的反应组合

    for train_index_rc, test_index_rc in kf.split(reactantCombination):
        break
    train_index = [
        i for rc in train_index_rc for i in reactantCombination[rc]]
    test_index = [
        i for rc in test_index_rc for i in reactantCombination[rc]]
    X_train, X_test = X[train_index], X[test_index]
    Y_train, Y_test = Y[train_index], Y[test_index]
    Y_test = numout2boolout(Y_test)
    score = [[[], [], []], [[], [], []]]
    for i in range(pace, len(train_index), pace):
        model = Model(**params)
        model.fit(X_train[:i], Y_train[:i])
        pred = model.predict(X_test)
        pred = numout2boolout(pred)
        ppred = model.predict(X_train[:i])
        ppred = numout2boolout(ppred)
        score[0][0].append(
            recall_score(Y_test, pred, average='weighted'))
        score[0][1].append(
            precision_score(Y_test, pred, average="weighted"))
        score[0][2].append(accuracy_score(Y_test, pred))

        score[1][0].append(
            recall_score(numout2boolout(Y_train[:i]), ppred, average='weighted'))
        score[1][1].append(
            precision_score(numout2boolout(Y_train[:i]), ppred, average="weighted"))
        score[1][2].append(accuracy_score(numout2boolout(Y_train[:i]), ppred))

    return score