
ALL_FIELDS = '__all__'


class STRICTNESS:
    class IGNORE:
        pass

    class RETURN_NO_RESULTS:
        pass

    class RAISE_VALIDATION_ERROR:
        pass

    # Values of False & True chosen for backward compatability reasons.
    # Originally, these were the only options.
    _LEGACY = {
        False: IGNORE,
        True: RETURN_NO_RESULTS,
        "RAISE": RAISE_VALIDATION_ERROR,
    }
