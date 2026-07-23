<p align="center">
  <img src="https://constellab.space/assets/fl-logo/constellab-logo-text-white.svg" alt="Constellab Logo" width="80%">
</p>

<br/>

# 👋 Welcome to GWS Gena

```gws_gena``` is a [Constellab](https://constellab.io) library (called bricks) developped by [Gencovery](https://gencovery.com/). GWS stands for Gencovery Web Services.

## 🚀 What is Constellab?

✨ [Gencovery](https://gencovery.com/) is a software company that offers [Constellab](https://constellab.io)., the leading open and secure digital infrastructure designed to consolidate data and unlock its full potential in the life sciences industry. Gencovery's mission is to provide universal access to data to enhance people's health and well-being.

🌍 With our Fair Open Access offer, you can use Constellab for free. [Sign up here](https://constellab.space/). Find more information about the Open Access offer here (link to be defined).

## ✅ Features

Gencovery brick to build, contextualize and simulate genome-scale metabolic models (GEMs) in Constellab, as a thin wrapper around the [cobrapy](https://github.com/opencobra/cobrapy) toolbox.
- Import a genome-scale metabolic model from a standard COBRA JSON file, or download one directly from the [BiGG Models](http://bigg.ucsd.edu) database
- Reconstruct a draft model from a list of EC numbers and/or an organism's NCBI taxonomy id, using curated reactions from the `gws_biota` database, then curate it with gap-filling, orphan removal and isolated-gene/reaction detection
- Contextualize a model ("Twin") with reaction bound constraints and soft flux targets, built from measured flux/phenotype tables or derived from differential gene expression (DEG) data
- Simulate a Twin with flux balance analysis (FBA), with an optional relaxed (quadratic) solver for partially curated models where a strict steady-state constraint would make the simulation infeasible
- Explore the solution space with flux variability analysis (FVA), and assess the impact of gene/reaction knockouts with knockout analysis (KOA)
- Reduce a Twin's network via elementary flux mode (EFM) analysis
- Guide the whole build/contextualize/simulate workflow through an interactive Streamlit dashboard app

## 📄 Documentation

📄  For `gws_gena` brick documentation, click [here](https://constellab.community/bricks/gws_gena/latest/doc/getting-started/65884539-69ef-4657-b23d-ae0a3f503e8e)

💫 For Constellab application documentation, click [here](https://constellab.community/bricks/gws_academy/latest/doc/getting-started/b38e4929-2e4f-469c-b47b-f9921a3d4c74)

## 🛠️ Installation

The `gws_gena` brick requires the `gws_core` and `gws_omix` bricks.

### 🔥 Recommended Method

The best way to install a brick is through the Constellab platform. With our Fair Open Access offer, you get a free cloud data lab where you can install bricks directly. [Sign up here](https://constellab.space/)

Learn about the data lab here : [Overview](https://constellab.community/bricks/gws_academy/latest/doc/digital-lab/overview/294e86b4-ce9a-4c56-b34e-61c9a9a8260d) and [Data lab management](https://constellab.community/bricks/gws_academy/latest/doc/digital-lab/on-cloud-digital-lab-management/4ab03b1f-a96d-4d7a-a733-ad1edf4fb53c)

### 🔧 Manual installation

This section is for users who want to install the brick manually. It can also be used to install the brick manually in the Constellab Codelab.

We recommend installing using Ubuntu 22.04 with python 3.10.

Required packages are listed in the ```settings.json``` file, for now the packages must be installed manually.

```bash
pip install cvxpy==1.5.2 efmtool==0.2.1 networkx==2.8.8
```

#### Usage

▶️ To start the server :

```bash
gws server run
```

🕵️ To run a given unit test

```bash
gws server test [TEST_FILE_NAME]
```

Replace `[TEST_FILE_NAME]` with the name of the test file (without `.py`) in the tests folder. Execute this command in the folder of the brick.

🕵️ To run the whole test suite, use the following command:

```bash
gws server test all
```

📌 VSCode users can use the predefined run configuration in `.vscode/launch.json`.

## 🤗 Community

🌍 Join the Constellab community [here](https://constellab.community/) to share and explore stories, code snippets and bricks with other users.

🚩 Feel free to open an issue if you have any question or suggestion.

☎️ If you have any questions or suggestions, please feel free to contact us through our website: [Constellab](https://constellab.io/).

## 🌎 License

```gws_gena``` is completely free and open-source and licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html).

<br/>

This brick is maintained with ❤️ by [Gencovery](https://gencovery.com/).

<p align="center">
  <img src="https://framerusercontent.com/images/Z4C5QHyqu5dmwnH32UEV2DoAEEo.png?scale-down-to=512" alt="Gencovery Logo"  width="30%">
</p>