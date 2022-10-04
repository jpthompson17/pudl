"""PyTest cases related to the integration between FERC1 & EIA 860/923."""
import logging
from pathlib import Path

import pandas as pd
import pytest

from pudl.glue.ferc1_eia import (
    get_raw_plants_ferc1,
    get_unmapped_plants_eia,
    get_unmapped_utils_eia,
    glue,
)
from pudl.glue.xbrl_dbf_ferc1 import (
    get_util_ids_ferc1_raw_xbrl,
    get_utils_ferc1_raw_dbf,
)
from pudl.metadata.classes import DataSource

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def glue_dfs() -> dict[str, pd.DataFrame]:
    """Make a dictionary of glue dataframes."""
    return glue(eia=True, ferc1=True)


@pytest.fixture(scope="module")
def utilities_pudl(glue_dfs) -> pd.DataFrame:
    """A table of PUDL utilities IDs."""
    return glue_dfs["utilities_pudl"]


@pytest.fixture(scope="module")
def utilities_ferc1(glue_dfs) -> pd.DataFrame:
    """A table of FERC1 utilities IDs."""
    return glue_dfs["utilities_ferc1"]


@pytest.fixture(scope="module")
def utilities_ferc1_xbrl(glue_dfs) -> pd.DataFrame:
    """A table of FERC1 XBRL utilities IDs."""
    return glue_dfs["utilities_ferc1_xbrl"]


@pytest.fixture(scope="module")
def utilities_ferc1_dbf(glue_dfs) -> pd.DataFrame:
    """A table of FERC1 DBF utilities IDs."""
    return glue_dfs["utilities_ferc1_dbf"]


@pytest.fixture(scope="module")
def plants_pudl(glue_dfs) -> pd.DataFrame:
    """A table of FERC1 DBF utilities IDs."""
    return glue_dfs["plants_pudl"]


@pytest.fixture(scope="module")
def plants_ferc1(glue_dfs) -> pd.DataFrame:
    """A table of FERC1 DBF utilities IDs."""
    return glue_dfs["plants_ferc1"]


# Raw FERC1 db utilities/plants


@pytest.fixture(scope="module")
def util_ids_ferc1_raw_xbrl(ferc1_xbrl_engine):
    """A fixture of utilty ids from the raw XBRL db."""
    return get_util_ids_ferc1_raw_xbrl(ferc1_xbrl_engine)


@pytest.fixture(scope="module")
def util_ids_ferc1_raw_dbf(ferc1_dbf_engine):
    """A fixture of utilty ids from the raw XBRL db."""
    return get_utils_ferc1_raw_dbf(ferc1_dbf_engine)


@pytest.fixture(scope="module")
def plants_ferc1_raw(pudl_settings_fixture):
    """A fixture of raw FERC1 plants."""
    return get_raw_plants_ferc1(
        pudl_settings=pudl_settings_fixture,
        years=DataSource.from_id("ferc1").working_partitions["years"],
    )


def get_missing_ids(
    ids_left: pd.DataFrame,
    ids_right: pd.DataFrame,
    id_cols: list[str],
):
    """Identify IDs that are missing from the left df but show up in the right df."""
    id_test = pd.merge(ids_left, ids_right, on=id_cols, indicator=True, how="outer")
    missing = id_test[id_test._merge == "right_only"]
    return missing


ID_PARAMETERS = [
    pytest.param(
        "utilities_pudl",
        "utilities_ferc1",
        ["utility_id_pudl"],
        id="validate_utility_id_pudl_in_utilities_ferc1",
    ),
    pytest.param(
        "utilities_ferc1",
        "utilities_ferc1_dbf",
        ["utility_id_ferc1"],
        id="validate_utility_id_ferc1_in_utilities_ferc1_dbf",
    ),
    pytest.param(
        "utilities_ferc1",
        "utilities_ferc1_xbrl",
        ["utility_id_ferc1"],
        id="validate_utility_id_ferc1_in_utilities_ferc1_xbrl",
    ),
    pytest.param(
        "utilities_ferc1",
        "plants_ferc1",
        ["utility_id_ferc1"],
        id="validate_utility_id_ferc1_in_plants_ferc1",
    ),
    pytest.param(
        "utilities_ferc1_xbrl",
        "util_ids_ferc1_raw_xbrl",
        ["utility_id_ferc1_xbrl"],
        id="check_for_unmmaped_utility_id_ferc1_xbrl_in_raw_xbrl",
    ),
    pytest.param(
        "utilities_ferc1_dbf",
        "util_ids_ferc1_raw_dbf",
        ["utility_id_ferc1_dbf"],
        id="check_for_unmmaped_utility_id_ferc1_dbf_in_raw_dbf",
    ),
    pytest.param(
        "plants_pudl",
        "plants_ferc1",
        ["plant_id_pudl"],
        id="validate_plant_id_pudl_in_plants_ferc1",
    ),
    pytest.param(
        "plants_ferc1",
        "plants_ferc1_raw",
        ["utility_id_ferc1", "plant_name_ferc1"],
        id="check_for_unmmapped_plants_in_plants_ferc1",
    ),
]


@pytest.mark.parametrize("ids_left,ids_right,id_cols", ID_PARAMETERS)
def test_for_fk_validation_and_unmapped_ids(
    ids_left: str,
    ids_right: str,
    id_cols: list[str],
    save_unmapped_ids,
    test_dir,
    request,
):
    """Test that the stored ids are internally consistent.

    Args:
        ids_left: name of fixure cooresponding to a dataframe which contains ID's
        ids_right: name of fixure cooresponding to a dataframe which contains ID's
        id_cols: list of ID column(s)

    Raises:
        AssertionError:
    """
    missing = get_missing_ids(
        request.getfixturevalue(ids_left),
        request.getfixturevalue(ids_right),
        id_cols,
    )
    print(request.node.callspec.id)
    if save_unmapped_ids:
        file_path = Path(
            test_dir.parent,
            "devtools",
            "ferc1-eia-glue",
            f"{request.node.callspec.id}.csv",
        )
        missing.to_csv(file_path)
    if not missing.empty:
        raise AssertionError(f"Found {len(missing)} {id_cols}: {missing}")


@pytest.mark.parametrize(
    "ids_left,ids_right,id_cols,drop",
    [
        pytest.param(
            "plants_ferc1",
            "plants_ferc1_raw",
            ["utility_id_ferc1", "plant_name_ferc1"],
            (227, "comanche"),
            id="check_for_unmmapped_plants_in_plants_ferc1",
        ),
        pytest.param(
            "utilities_ferc1",
            "utilities_ferc1_xbrl",
            ["utility_id_ferc1"],
            (227),
            id="validate_utility_id_ferc1_in_utilities_ferc1_xbrl",
        ),
    ],
)
def test_for_unmapped_ids_minus_one(
    ids_left: str, ids_right: str, id_cols: list[str], drop: tuple, request
):
    """Test that we will find one unmapped ID after dropping one.

    Args:
        ids_left: name of fixure cooresponding to a dataframe which contains ID's
        ids_right: name of fixure cooresponding to a dataframe which contains ID's
        id_cols: list of ID column(s)
        drop: a tuple of the one record IDs to drop

    Raises:
        AssertionError:
    """
    ids_minus_one = (
        request.getfixturevalue(ids_left).set_index(id_cols).drop(drop).reset_index()
    )
    missing = get_missing_ids(
        ids_minus_one, request.getfixturevalue(ids_right), id_cols
    )
    if len(missing) != 1:
        raise AssertionError(f"Found {len(missing)} {id_cols} but expected 1.")


def test_unmapped_plants_eia(pudl_settings_fixture, pudl_engine):
    """Check for unmapped EIA Plants."""
    unmapped_plants_eia = get_unmapped_plants_eia(pudl_engine)
    if not unmapped_plants_eia.empty:
        raise AssertionError(
            f"Found {len(unmapped_plants_eia)} unmapped EIA plants, expected 0."
            f"{unmapped_plants_eia}"
        )


def test_unmapped_utils_eia(pudl_settings_fixture, pudl_engine):
    """Check for unmapped EIA Plants."""
    unmapped_utils_eia = get_unmapped_utils_eia(pudl_engine)
    if not unmapped_utils_eia.empty:
        raise AssertionError(
            f"Found {len(unmapped_utils_eia)} unmapped EIA utilities, expected 0."
            f"{unmapped_utils_eia}"
        )
