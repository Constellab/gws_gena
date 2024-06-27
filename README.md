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

GENA is a powerful tool for genome-scale metabolic modeling, designed to facilitate the analysis and simulation of metabolic networks. It enables researchers to understand complex biological systems, predict metabolic behavior, and identify potential metabolic engineering targets.

- **Comprehensive Modeling**: Supports the construction and analysis of genome-scale metabolic models.
- **Predictive Insights**: Enables accurate predictions of metabolic behavior and phenotypic outcomes.
- **User-Friendly Interface**: Intuitive design for easy setup and use, suitable for both novice and experienced users.
- **Flexible and Scalable**: Adaptable to a wide range of research projects, from small-scale studies to extensive genome-wide analyses.
Explore how GENA can enhance your research in metabolic engineering, systems biology, and synthetic biology.

**Installation and Usage Instructions**:

1. **Download**: Clone or download the repository.
2. **Documentation**: Detailed documentation is available at [Constellab Community](https://constellab.community).
3. **Build Models**: Construct genome-scale metabolic models using provided datasets and tools.
4. **Analyze and Simulate**: Utilize GENA’s features to analyze metabolic networks and simulate various conditions.

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
pip install cvxpy==1.3.0 efmtool==0.2.0 networkx==2.8.8 bioservices==1.11.2
```

#### Usage

▶️ To start the server :

```bash
python3 manage.py --runserver
```

🕵️ To run a given unit test

```bash
python3 manage.py --test [TEST_FILE_NAME]
```

Replace `[TEST_FILE_NAME]` with the name of the test file (without `.py`) in the tests folder.

🕵️ To run the whole test suite, use the following command:

```bash
python3 manage.py --test all
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