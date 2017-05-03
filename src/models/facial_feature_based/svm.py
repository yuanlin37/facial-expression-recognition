import multiprocessing
from functools import partial

import numpy as np
from sklearn.svm import SVC
from sklearn.preprocessing import scale

from src.extract_data.get_data_from_csv import GetDataFromCSV
from src.pre_processing.extract_landscape import get_facial_vectors
from src.models.facial_feature_based.common import get_normalized_vectors
from src.models.facial_feature_based.common import clean_normalized_vectors


def svc_at_gamma(scaled_clean_normalized_vectors_train,
                 clean_targets_train,
                 scaled_clean_normalized_vectors_test,
                 clean_targets_test,
                 new_gamma
                 ):
    C_range = np.logspace(-2, 10, 13)
    for C in C_range:
        # ok, we're basically ready to go, split it in to the correct splits
        # and we can train/test.

        classifier = SVC(C=C, verbose=True, gamma=new_gamma)
        classifier.fit(scaled_clean_normalized_vectors_train,
                       clean_targets_train)

        train_score = classifier.score(scaled_clean_normalized_vectors_train,
                                       clean_targets_train)
        test_score = classifier.score(scaled_clean_normalized_vectors_test,
                                      clean_targets_test)
        test_predictions = classifier.predict(
            scaled_clean_normalized_vectors_test
        )

        filename = "results/svm_with_gamma_%s_C_%s.csv" % (new_gamma,
                                                           C_range)
        with open(filename, 'w') as outfile:
            outfile.write("train_score:%s, test_score:%s\n" % (train_score,
                                                               test_score))
            for prediction in test_predictions.tolist():
                outfile.write("%s\n" % str(prediction))
            outfile.flush()


def run():
    print("reading csv data, cached or not")
    csv_reader = GetDataFromCSV()
    facial_pixels_train, targets_train = csv_reader.get_training_data()
    facial_vectors_train = get_facial_vectors(only_train_data=True,
                                              load_cached=True)
    facial_pixels_test, targets_test = csv_reader.get_test_data()
    facial_vectors_test = get_facial_vectors(only_test_data=True,
                                             load_cached=True)

    # get our pixels in to a small vector based on facial features extracted
    # by dlib, gets them all concatenated in a single vector of pixels, after
    # this point, we can discard all other data except for targets.

    print("getting normalized/concatenated facial vectors")
    normalized_vectors_train, feature_target_sizes = get_normalized_vectors(
        facial_vectors_train,
        facial_pixels_train
    )
    normalized_vectors_test, _ = get_normalized_vectors(
        facial_vectors_test,
        facial_pixels_test,
        feature_target_sizes=feature_target_sizes
    )

    # clean a little first
    print("cleaning normalized/concatenated facial vectors up")
    clean_normalized_vectors_train, clean_targets_train, _ = clean_normalized_vectors(
        normalized_vectors_train, targets_train
    )
    clean_normalized_vectors_test, clean_targets_test, _ = clean_normalized_vectors(
        normalized_vectors_test, targets_test
    )

    scaled_clean_normalized_vectors_train = scale(clean_normalized_vectors_train)
    scaled_clean_normalized_vectors_test = scale(clean_normalized_vectors_test)

    gamma_range = np.logspace(-9, 3, 16)

    pool = multiprocessing.Pool(16)
    svc_run = partial(
        svc_at_gamma,
        scaled_clean_normalized_vectors_train,
        clean_targets_train,
        scaled_clean_normalized_vectors_test,
        clean_targets_test,
    )
    print("running")
    pool.map(svc_run, gamma_range)