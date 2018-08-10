#!/usr/bin/env python2

from ROOT import TH1F, TGraph, TH2F, TCanvas, TLegend
import array


class Plotter(object):

    def __init__(self):
        self.Plots = []


    def plot_histo(self, h, draw_opt='', lm=None, rm=None, l=None):
        c = TCanvas('c{n}'.format(n=h.GetName()), 'c', 1000, 1000)
        lm = c.GetLeftMargin() if lm is None else lm
        rm = c.GetRightMargin() if rm is None else rm
        c.SetMargin(lm, rm, .1, .1)
        h.Draw(draw_opt)
        if l is not None:
            l.Draw()
        self.Plots.append([h, c, l])

    @staticmethod
    def create_legend(x1=.65, y2=.88, nentries=2, scale=1, name='l', y1=None, margin=.25, x2=None):
        x2 = .88 if x2 is None else x2
        y1 = y2 - nentries * .05 * scale if y1 is None else y1
        l = TLegend(x1, y1, x2, y2)
        l.SetName(name)
        l.SetTextFont(42)
        l.SetTextSize(0.03 * scale)
        l.SetMargin(margin)
        return l

    @staticmethod
    def create_th1(data, minimum, maximum, name, x_title, y_title):
        th1 = TH1F(name, name, len(data), minimum, maximum)
        th1.SetDirectory(0)
        th1.GetXaxis().SetTitle(x_title)
        th1.GetYaxis().SetTitle(y_title)
        th1.SetDrawOption('HIST')
        th1.SetLineWidth(2)
        for ix, x in enumerate(data):
            th1.SetBinContent(ix, x)
        return th1

    @staticmethod
    def create_graph(x, y, name='gr', tit='', xtit='', ytit='', yoff=1.4, color=None):
        gr = TGraph(len(x), array.array('d', x), array.array('d', y))
        gr.SetNameTitle(name, tit)
        gr.SetMarkerStyle(20)
        gr.SetMarkerSize(1)
        xax = gr.GetXaxis()
        xax.SetTitle(xtit)
        yax = gr.GetYaxis()
        yax.SetTitle(ytit)
        yax.SetTitleOffset(yoff)
        if color is not None:
            gr.SetMarkerColor(color)
            gr.SetLineColor(color)
        return gr

    @staticmethod
    def create_tgraph(data, name, x_title, y_title, minimum=None, data_x=-1):
        #        xdata = list(xrange(len(data)))
        xdata = data_x
        if data_x == -1:
            xdata = []
            for i in range(len(data)):
                xdata.append(minimum + i)
        x = array.array('d', xdata)
        y = array.array('d', data)
        gr = TGraph(len(x), x, y)
        # gr.SetDirectory(0)
        gr.SetTitle(name)
        gr.SetLineColor(4)
        gr.SetMarkerColor(2)
        gr.SetMarkerSize(1.5)
        gr.SetMarkerStyle(34)
        gr.GetXaxis().SetTitle(x_title)
        gr.GetYaxis().SetTitle(y_title)
        gr.GetYaxis().SetTitleOffset(1.4)
        # gr.SetDrawOption('ALP')
        gr.SetLineWidth(2)
        return gr

    @staticmethod
    def create_th2(data, x_min, x_max, y_min, y_max, name, x_title, y_title, z_title):
        th2 = TH2F(name, name, data.shape[0], x_min, x_max, data.shape[1], y_min, y_max)
        th2.SetDirectory(0)
        th2.GetXaxis().SetTitle(x_title)
        th2.GetYaxis().SetTitle(y_title)
        th2.GetYaxis().SetTitleOffset(1.3)
        th2.GetZaxis().SetTitle(z_title)
        th2.SetDrawOption('COLZ')
        for ix, x in enumerate(data, 1):
            for iy, y in enumerate(x, 1):
                th2.SetBinContent(ix, iy, y)
        th2.GetZaxis().SetRangeUser(0, th2.GetMaximum())
        return th2

    def matrix_to_th2(d, name, x_title, y_title):
        dim = matrix.shape
        return self.create_th2(matrix, dim[0], dim[1], name, x_title, y_title)
