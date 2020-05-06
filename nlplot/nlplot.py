"""Visualization Module for Natural Language Processing

Todo:
    TODO:
    * create markdown for get started
    * hoge

Examples:

"""

import pandas as pd
import numpy as np
import itertools
import os
import gc
import multiprocessing
from collections import defaultdict, Counter
from tqdm import tqdm
from sklearn import preprocessing
import datetime as datetime
import warnings
warnings.filterwarnings('ignore')
warnings.simplefilter('ignore')

import gensim
import pyLDAvis.gensim
pyLDAvis.enable_notebook()

import seaborn as sns
import plotly
import plotly.graph_objs as go
import plotly.express as px
from plotly.offline import iplot
from wordcloud import WordCloud
import IPython.display
from io import BytesIO
from PIL import Image
import networkx as nx
from networkx.algorithms import community

TTF_FILE_NAME = 'mplus-1c-regular.ttf'


def get_colorpalette(colorpalette, n_colors):
    """Get a color palette"""
    palette = sns.color_palette(
        colorpalette, n_colors)
    rgb = ['rgb({},{},{})'.format(*[x*256 for x in rgb]) for rgb in palette]
    return rgb


def freq_df(df_value, n_gram=1, n=50, stopwords=[], verbose=True):
    """Create a data frame of frequent word"""

    # Function to create a list of n-grams
    def generate_ngrams(text, n_gram=1):
        token = [token for token in text.lower().split(" ") if token != "" if token not in stopwords]
        ngrams = zip(*[token[i:] for i in range(n_gram)])
        return [" ".join(ngram) for ngram in ngrams]

    freq_dict = defaultdict(int)
    if verbose:
        for sent in tqdm(df_value):
            for word in generate_ngrams(str(sent), n_gram=n_gram):
                freq_dict[word] += 1
    else:
        for sent in df_value:
            for word in generate_ngrams(str(sent), n_gram=n_gram):
                freq_dict[word] += 1

    fd_sorted = pd.DataFrame(sorted(freq_dict.items(), key=lambda x: x[1])[::-1])
    fd_sorted.columns = ['word', 'word_count']
    return fd_sorted.head(n)


class NLPlot():
    """Visualization Module for Natural Language Processing

    Attributes:
        df (pd.DataFrame): Original data frame to be graphed
        taget_col: Columns to be analyzed that exist in df (assuming type list) e.g. [hoge, fuga, ...]
        html_file_path: path to save the html file of the generated graph
        default_stopwords_file_path: The path to the file that defines the default stopword
    """

    def __init__(self, df, taget_col, html_file_path='./', default_stopwords_file_path=''):
        """init"""
        self.df = df
        self.taget_col = taget_col
        self.df.dropna(subset=[self.taget_col], inplace=True)
        self.df[self.taget_col] = self.df[self.taget_col].map(lambda x: x.split())
        self.df[self.taget_col + '_length'] = self.df[self.taget_col].map(lambda x: len(x))
        self.html_file_path = html_file_path
        self.default_stopwords = []
        if os.path.exists(default_stopwords_file_path):
            f = open(default_stopwords_file_path)
            txt_file = f.readlines()
            f.close()
            self.default_stopwords = [line.strip() for line in txt_file]

    def get_stopword(self, top_n=10, bottom_n=3) -> list:
        """Calculate the stop word.

        Calculate the top_n words with the highest number of occurrences
        and the words that occur only below the bottom_n as stopwords.

        Args:
            docs (list or Series of str): docs (split space)
            top_n (int): Top N of the number of occurrences of words to exclude
            bottom_n (int): Bottom of the number of occurrences of words to exclude

        Returns:
            list: list of stop words

        """
        fdist = Counter()

        # Count the number of occurrences per word.
        for doc in self.df[self.taget_col]:
            for word in doc:
                fdist[word] += 1
        common_words = {word for word, freq in fdist.most_common(top_n)}  # 出現回数の多い単語
        rare_words = {word for word, freq in fdist.items() if freq <= bottom_n}  # 出現回数の少ない単語
        stopwords = list(common_words.union(rare_words))
        return stopwords

    def bar_ngram(self, stopwords=[], title=None,
                  xaxis_label='', yaxis_label='',
                  ngram=1, top_n=50, width=800, height=1500,
                  color=None, horizon=True, verbose=True, save=False) -> None:
        """Plots of n-gram bar chart

        Args:
            stopwords (list): A list of words to specify for the stopword.
            title (str): title of plot
            gram (int): N number of N grams
            top_n (int): How many words should be output
            save (bool): Whether or not to save the HTML file.

        """

        stopwords += self.default_stopwords

        _df = self.df.copy()
        _df['space'] = self.df[self.taget_col].apply(lambda x: ' '.join(x))

        # word count
        _df = freq_df(_df['space'], n_gram=ngram, n=top_n, stopwords=stopwords, verbose=verbose)

        if horizon:
            fig = px.bar(
                _df.sort_values('word_count'),
                y='word',
                x='word_count',
                text='word_count',
                orientation='h',)
        else:
            fig = px.bar(
                _df,
                y='word_count',
                x='word',
                text='word_count',)

        fig.update_traces(
            texttemplate='%{text:.2s}',
            textposition='auto',
            marker_color=color,)
        fig.update_layout(
            title=str(title),
            xaxis_title=str(xaxis_label),
            yaxis_title=str(yaxis_label),
            width=width,
            height=height,)
        fig.show()

        if save:
            self.save_plot(fig, title)

        del _df
        gc.collect()
        return None

    def treemap(self, stopwords=[], title=None, ngram=1, top_n=50,
                width=800, height=1500, verbose=True, save=False) -> None:
        """Plots of Tree Map"""

        stopwords += self.default_stopwords

        _df = self.df.copy()
        _df['space'] = self.df[self.taget_col].apply(lambda x: ' '.join(x))

        # word count
        _df = freq_df(_df['space'], n_gram=ngram, n=top_n, stopwords=stopwords, verbose=verbose)

        fig = px.treemap(
            _df,
            path=['word'],
            values='word_count',
        )
        fig.update_layout(
            title=str(title),
            width=width,
            height=height,
        )
        fig.show()

        if save:
            self.save_plot(fig, title)

        del _df
        return None

    def word_distribution(self, title=None,
                          xaxis_label='', yaxis_label='',
                          width=1000, height=500,
                          color=None, template='plotly', bins=None, save=False) -> None:
        """Plots of word count histogram

        Args:
            title (str): グラフのタイトル
            x_axis (str): x軸に指定するカラム
            x_label (str): 図形のx軸に設定するカラム名
            x_date (bool): x_axisがDate型の時にTrueとすると、YYYY-MM-DD表記になる
            save (bool): 図形をhtml形式で保存するか否か
            template (str): plotlyの描画スタイル

        """
        _df = self.df.copy()
        fig = px.histogram(_df, x=self.taget_col+'_length', color=color, template=template, nbins=bins)
        fig.update_layout(
            title=str(title),
            xaxis_title=str(xaxis_label),
            yaxis_title=str(yaxis_label),
            width=width,
            height=height)

        fig.show()

        if save:
            self.save_plot(fig, title)

        del _df
        return None

    def wordcloud(self, stopwords=[], width=800, height=500,
                  max_words=100, max_font_size=80,
                  colormap=None, mask_file=None, save=False):
        """Plots of WordCloud"""

        f_path = TTF_FILE_NAME
        if mask_file is not None:
            mask = np.array(Image.open(mask_file))
        else:
            mask = None

        _df = self.df.copy()
        text = _df[self.taget_col]
        stopwords += self.default_stopwords

        wordcloud = WordCloud(
                        background_color='white',
                        font_step=1,
                        contour_width=0,
                        contour_color='steelblue',
                        font_path=f_path,
                        stopwords=stopwords,
                        max_words=max_words,
                        max_font_size=max_font_size,
                        random_state=42,
                        width=width,
                        height=height,
                        mask=mask,
                        collocations=False,
                        prefer_horizontal=1,
                        colormap=colormap)
        wordcloud.generate(str(text))

        def show_array(img):
            stream = BytesIO()
            if save:
                Image.fromarray(img).save('wordcloud.png')
            Image.fromarray(img).save(stream, 'png')
            IPython.display.display(IPython.display.Image(data=stream.getvalue()))

        img = wordcloud.to_array()
        show_array(img)

        del _df
        gc.collect()
        return None

    def get_edges_nodes(self, batches, min_edge_frequency) -> None:
        """Generating the Edge and Node data frames for a graph

        Args:
            batches (list): array of word lists
            min_edge_frequency (int): Minimum number of edge occurrences. Edges less than this number will be removed.

        Returns:
            None

        """

        # sort function
        def _ranked_topics(batches):
            batches.sort()
            return batches

        # craeted unique combinations
        # e.g. [('hoge1', 'hoge2'), ('hoge1', 'hoge3'), ...]
        def _unique_combinations(batches):
            return list(itertools.combinations(_ranked_topics(batches), 2))

        # Calculate how many times the combination appears and store it in a dictionary
        def _add_unique_combinations(_unique_combinations, _dict):
            for combination in _unique_combinations:
                if combination in _dict:
                    _dict[combination] += 1
                else:
                    _dict[combination] = 1
            return _dict

        edge_dict = {}
        source = []
        target = []
        edge_frequency = []
        for batch in batches:
            # e.g. {('hoge1', 'hoge2'): 8, ('hoge1', 'hoge3'): 3, ...}
            edge_dict = _add_unique_combinations(_unique_combinations(batch), edge_dict)

        # create edge dataframe
        for key, value in edge_dict.items():
            source.append(key[0])
            target.append(key[1])
            edge_frequency.append(value)
        edge_df = pd.DataFrame({'source': source, 'target': target, 'edge_frequency': edge_frequency})
        edge_df.sort_values(by='edge_frequency', ascending=False, inplace=True)
        edge_df.reset_index(drop=True, inplace=True)
        edge_df = edge_df[edge_df['edge_frequency'] > min_edge_frequency]

        # create node dataframe
        node_df = pd.DataFrame({'id': list(set(list(edge_df['source']) + list(edge_df['target'])))})
        labels = [i for i in range(len(node_df['id']))]
        node_df['id_code'] = node_df.index
        node_dict = dict(zip(node_df['id'], labels))

        edge_df['source_code'] = edge_df['source'].apply(lambda x: node_dict[x])
        edge_df['target_code'] = edge_df['target'].apply(lambda x: node_dict[x])

        self.edge_df = edge_df
        self.node_df = node_df
        self.node_dict = node_dict
        self.edge_dict = edge_dict

        return None

    def get_graph(self) -> nx.Graph:
        """create Networkx

        Returns:
            nx.Graph(): Networkx graph
        """

        def _extract_edges(edge_df):
            tuple_out = []
            for i in range(0, len(self.edge_df.index)):
                tuple_out.append((self.edge_df['source_code'][i], self.edge_df['target_code'][i]))
            return tuple_out

        # Networkx graph
        G = nx.Graph()

        # Add Node from Data Frame
        G.add_nodes_from(self.node_df.id_code)

        # Add Edge from Data Frame
        # e.g. [(8, 47), (4, 47), (47, 0), ...]
        edge_tuples = _extract_edges(self.edge_df)
        for i in edge_tuples:
            G.add_edge(i[0], i[1])

        return G

    def build_graph(self, stopwords=[], min_edge_frequency=10) -> None:
        """Preprocessing to output a co-occurrence network

        Args:
            stopwords (list): List of words to exclude
            min_edge_frequency (int): Minimum number of edge occurrences (edges with fewer than this number are excluded)

        Returns:
            None

        """

        self.df_edit = self.df.copy()

        # Remove duplicates from the list to be analyzed
        self.df_edit[self.taget_col] = self.df_edit[self.taget_col].map(lambda x: list(set(x)))

        # Acquire only the column data for this analysis.
        self.target = self.df_edit[[self.taget_col]]

        # Get an array of word lists by excluding stop words
        # [['hoge1', 'hoge4', 'hoge7', 'hoge5'],
        #  ['hoge7', 'hoge2', 'hoge9', 'hoge12', 'hoge4'],...]
        stopwords += self.default_stopwords

        def _removestop(words):
            for stop_word in stopwords:
                try:
                    words.remove(stop_word)
                    words = words
                except:
                    pass
            return words
        batch = self.target[self.taget_col].map(_removestop)
        batches = batch.values.tolist()

        # Generating the Edge and Node data frames for a graph
        self.get_edges_nodes(batches, min_edge_frequency)

        # create adjacency, centrality, cluster
        # ref:
        # https://networkx.github.io/documentation/stable/reference/classes/generated/networkx.Graph.adjacency.html?highlight=adjacency#networkx.Graph.adjacency
        # https://networkx.github.io/documentation/networkx-1.10/reference/generated/networkx.algorithms.centrality.betweenness_centrality.html#betweenness-centrality
        # https://networkx.github.io/documentation/networkx-1.10/reference/generated/networkx.algorithms.cluster.clustering.html?highlight=clustering#clustering
        self.G = self.get_graph()
        self.adjacencies = dict(self.G.adjacency())
        self.betweeness = nx.betweenness_centrality(self.G)
        self.clustering_coeff = nx.clustering(self.G)
        self.node_df['adjacency_frequency'] = self.node_df['id_code'].map(lambda x: len(self.adjacencies[x]))
        self.node_df['betweeness_centrality'] = self.node_df['id_code'].map(lambda x: self.betweeness[x])
        self.node_df['clustering_coefficient'] = self.node_df['id_code'].map(lambda x: self.clustering_coeff[x])

        # create community
        # ref: https://networkx.github.io/documentation/stable/reference/algorithms/community.html#module-networkx.algorithms.community.modularity_max
        self.communities = community.greedy_modularity_communities(self.G)
        self.communities_dict = {}
        nodes_in_community = [list(i) for i in self.communities]
        for i in nodes_in_community:
            self.communities_dict[nodes_in_community.index(i)] = i

        def community_allocation(source_val):
            for k, v in self.communities_dict.items():
                if source_val in v:
                    return k

        self.node_df['community'] = self.node_df['id_code'].map(lambda x: community_allocation(x))

        return None

    def co_network(self, title, sizing=100, node_size='adjacency_frequency',
                   color_palette='hls', layout=nx.kamada_kawai_layout,
                   light_theme=True, width=1700, height=1200, save=False) -> None:
        """Plots of co-occurrence networks
        color_palette:https://qiita.com/SaitoTsutomu/items/c79c9973a92e1e2c77a7
        """

        # formatting options for plot - dark vs. light theme
        if light_theme:
            back_col = '#ffffff'
            edge_col = '#ece8e8'
        else:
            back_col = '#000000'
            edge_col = '#2d2b2b'

        # select of node_df -> ['adjacency_frequency', 'betweeness_centrality', 'clustering_coefficient']
        X = self.node_df[self.node_df.columns[2:5]]
        cols = self.node_df.columns[2:5]

        # scaling
        min_max_scaler = preprocessing.MinMaxScaler()
        X_scaled = min_max_scaler.fit_transform(X)
        _df = pd.DataFrame(X_scaled)
        _df.columns = cols

        for i in _df.columns:
            _df[i] = _df[i].apply(lambda x: x*sizing)

        # extract graph x,y co-ordinates from G instance
        pos = layout(self.G)

        # add position of each node from G to 'pos' key
        for node in self.G.nodes:
            self.G.nodes[node]['pos'] = list(pos[node])

        stack = []
        index = 0

        # add edges to Plotly go.Scatter object
        for edge in self.G.edges:
            x0, y0 = self.G.nodes[edge[0]]['pos']
            x1, y1 = self.G.nodes[edge[1]]['pos']
            weight = 1.2
            trace = go.Scatter(x=tuple([x0, x1, None]), y=tuple([y0, y1, None]),
                               mode='lines',
                               line={'width': weight},
                               marker=dict(color=edge_col),
                               line_shape='spline',
                               opacity=1)

            # append edge traces
            stack.append(trace)

            index = index + 1

        # make a partly empty dictionary for the nodes
        marker = {'size': [], 'line': dict(width=0.5, color=edge_col), 'color': []}

        # initialise a go.Scatter object for the nodes
        node_trace = go.Scatter(x=[], y=[], hovertext=[], text=[],
                                mode='markers+text', textposition='bottom center',
                                hoverinfo="text", marker=marker)

        index = 0

        n_legends = len(self.node_df['community'].unique())
        colors = get_colorpalette(color_palette, n_legends)

        # add nodes to Plotly go.Scatter object
        for node in self.G.nodes():

            x, y = self.G.nodes[node]['pos']
            node_trace['x'] += tuple([x])
            node_trace['y'] += tuple([y])
            node_trace['text'] += tuple([self.node_df['id'][index]])

            # Change the color scheme for each community
            for i in range(n_legends):
                if self.node_df.community[index] == i:
                    node_trace['marker']['color'] += tuple([list(colors)[i]])
            node_trace['marker']['size'] += tuple([list(_df[node_size])[index]])

            index = index + 1

        # append node traces
        stack.append(node_trace)

        # set up axis for plot
        # hide axis line, grid, ticklabels and title
        axis = dict(showline=False,
                    zeroline=False,
                    showgrid=False,
                    showticklabels=False,
                    title='')

        # set up figure for plot
        fig = {
            "data": stack,
            "layout":
                go.Layout(title=str(title),
                          font=dict(family='Arial', size=12),
                          width=width,
                          height=height,
                          autosize=True,
                          showlegend=False,
                          xaxis=axis,
                          yaxis=axis,
                          margin=dict(l=40, r=40, b=85, t=100, pad=0),
                          hovermode='closest',
                          plot_bgcolor=back_col,  # set background color
                          )
        }
        iplot(fig)

        if save:
            self.save_plot(fig, title)

        del _df
        gc.collect()
        return None

    def sunburst(self, title, colorscale=False, color_col='betweeness_centrality', width=1300, height=1300, save=False) -> None:
        """Plots of sunburst chart
        """

        # make copy of node dataframe
        _df = self.node_df.copy()

        # change community label to string (needed for plot)
        _df['community'] = _df['community'].map(lambda x: str(x))

        # conditionals for plot type
        if colorscale is False:
            fig = px.sunburst(_df, path=['community', 'id'], values='adjacency_frequency',
                              color='community', hover_name=None, hover_data=None)
        else:
            # color scale:https://plotly.com/python/builtin-colorscales/
            fig = px.sunburst(_df, path=['community', 'id'], values='adjacency_frequency',
                              color=color_col, hover_data=None,
                              color_continuous_scale='Oryel',
                              color_continuous_midpoint=np.average(_df[color_col],
                              weights=_df[color_col]))

        fig.update_layout(
            title=str(title),
            width=width,
            height=height,)
        fig.show()

        if save:
            self.save_plot(fig, title)

        del _df
        gc.collect()
        return None

    def ldavis(self, num_topics, passes, save=False) -> pyLDAvis:
        """Plots of pyLDAvis

        ref: https://github.com/bmabey/pyLDAvis

        """

        workers = multiprocessing.cpu_count()
        workers = workers if workers == 1 else int(workers/2)

        dic = gensim.corpora.Dictionary(self.df[self.taget_col])
        bow_corpus = [dic.doc2bow(doc) for doc in self.df[self.taget_col]]

        lda_model = gensim.models.LdaMulticore(bow_corpus,
                                               num_topics=num_topics,
                                               id2word=dic,
                                               passes=passes,
                                               workers=workers,
                                               random_state=0)

        vis = pyLDAvis.gensim.prepare(lda_model, bow_corpus, dic)

        if save:
            date = str(pd.to_datetime(datetime.datetime.now())).split(' ')[0]
            filename = date + '_' + 'pyldavis.html'
            pyLDAvis.save_html(vis, filename)

        return vis

    def save_plot(self, fig, title) -> None:
        date = str(pd.to_datetime(datetime.datetime.now())).split(' ')[0]
        filename = date + '_' + str(title) + '.html'
        filename = self.html_file_path + filename
        plotly.offline.plot(fig, filename=filename, auto_open=False)
        # plotly.offline.plot(plot_save, filename=filename, image_filename=filename, image='jpeg')
        return None

    def save_tables(self) -> None:

        date = str(pd.to_datetime(datetime.datetime.now())).split(' ')[0]

        self.node_df.to_csv(date + "_node_df_" + self.source + ".csv", index=False)
        print('Saved nodes')
        self.edge_df.to_csv(date + "_edge_df_" + self.source + ".csv", index=False)
        print('Saved edges')
        self.df_edit.to_csv(date + "_df_edit_" + self.source + ".csv", index=False)
        print('Saved edited dataframe')
        self.df.to_csv(date + "_df_" + self.source + "_.csv", index=False)
        print('Saved unedited dataframe')

        return None
