
ALL_FIELDS = '__all__'


EMPTY_VALUES = ([], (), {}, '', None)


class STRICTNESS(object):
    class IGNORE(object):
        pass

    class RETURN_NO_RESULTS(object):
        pass

    class RAISE_VALIDATION_ERROR(object):
        pass

    # Values of False & True chosen for backward compatability reasons.
    # Originally, these were the only options.
    _LEGACY = {
        False: IGNORE,
        True: RETURN_NO_RESULTS,
        "RAISE": RAISE_VALIDATION_ERROR,
    }
