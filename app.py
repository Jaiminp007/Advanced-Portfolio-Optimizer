"""
Modern Portfolio Theory Optimizer - Flask Backend
Advanced portfolio optimization with multiple strategies and risk analysis
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from datetime import datetime, timedelta
import json
import sqlite3
import os
from io import BytesIO
import base64

import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend suitable for server rendering
import matplotlib.pyplot as plt

app = Flask(__name__)
CORS(app)

# Database initialization
def init_db():
    """Initialize SQLite database for storing portfolio history"""
    conn = sqlite3.connect('portfolio.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS optimizations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  tickers TEXT,
                  strategy TEXT,
                  optimal_weights TEXT,
                  expected_return REAL,
                  volatility REAL,
                  sharpe_ratio REAL,
                  risk_free_rate REAL)''')
    conn.commit()
    conn.close()

init_db()

# Mock historical price data (expanded dataset)
MOCK_PRICE_DATA = {
    'AAPL': [170.15, 171.23, 170.50, 172.45, 173.20, 171.80, 172.90, 174.25, 173.50, 175.10, 176.35, 175.20, 177.45, 178.90, 177.30, 179.50, 180.25, 181.40, 180.15, 182.30, 183.55, 182.10, 184.20, 185.45, 186.70, 185.30, 187.15, 188.90, 187.45, 189.70, 191.25, 190.10, 192.35, 193.80, 192.45, 194.60, 195.90, 194.25, 196.45, 197.80, 196.30, 198.55, 199.90, 198.45, 200.70, 202.15, 200.80, 203.25, 204.60, 203.15, 205.40, 206.85, 205.50, 207.75, 209.20, 207.85, 210.10, 211.55, 210.20, 212.45, 213.90, 212.55, 214.80, 216.25, 214.90, 217.15, 218.60, 217.25, 219.50, 220.95, 219.60, 221.85, 223.30, 221.95, 224.20, 225.65, 224.30, 226.55, 228.00, 226.65, 228.90, 230.35, 229.00, 231.25, 232.70, 231.35, 233.60, 235.05, 233.70, 235.95, 237.40, 236.05, 238.30, 239.75, 238.40, 240.65, 242.10, 240.75, 243.00, 244.45, 178.25, 179.80, 178.35, 180.60, 182.05, 180.70, 182.95, 184.40, 183.05, 185.30, 186.75, 185.40, 187.65, 189.10, 187.75, 190.00, 191.45, 190.10, 192.35, 193.80, 192.45, 194.70, 196.15, 194.80, 197.05, 198.50, 197.15, 199.40, 200.85, 199.50, 201.75, 203.20, 201.85, 204.10, 205.55, 204.20, 206.45, 207.90, 206.55, 208.80, 210.25, 208.90, 211.15, 212.60, 211.25, 213.50, 214.95, 213.60, 215.85, 217.30, 215.95, 218.20, 219.65, 218.30, 220.55, 222.00, 220.65, 222.90, 224.35, 223.00, 225.25, 226.70, 225.35, 227.60, 229.05, 227.70, 229.95, 231.40, 230.05, 232.30, 233.75, 232.40, 234.65, 236.10, 234.75, 237.00, 238.45, 237.10, 239.35, 240.80, 239.45, 241.70, 243.15, 241.80, 244.05, 245.50, 244.15, 246.40, 247.85, 246.50, 248.75, 250.20, 248.85, 251.10, 252.55, 251.20, 253.45, 254.90, 253.55, 255.80, 257.25, 255.90, 258.15, 259.60, 258.25, 260.50, 261.95, 260.60, 262.85, 264.30, 262.95, 265.20, 266.65, 265.30, 267.55, 269.00, 267.65, 269.90, 271.35, 270.00, 272.25, 273.70, 272.35, 274.60, 276.05, 274.70, 276.95, 278.40, 277.05, 279.30, 280.75, 279.40, 281.65, 283.10, 281.75, 284.00, 285.45, 284.10, 286.35, 287.80, 286.45, 288.70, 290.15],
    'MSFT': [300.80, 301.50, 302.75, 301.20, 303.45, 304.90, 303.55, 305.80, 307.25, 305.90, 308.15, 309.60, 308.25, 310.50, 311.95, 310.60, 312.85, 314.30, 312.95, 315.20, 316.65, 315.30, 317.55, 319.00, 317.65, 319.90, 321.35, 320.00, 322.25, 323.70, 322.35, 324.60, 326.05, 324.70, 326.95, 328.40, 327.05, 329.30, 330.75, 329.40, 331.65, 333.10, 331.75, 334.00, 335.45, 334.10, 336.35, 337.80, 336.45, 338.70, 340.15, 338.80, 341.05, 342.50, 341.15, 343.40, 344.85, 343.50, 345.75, 347.20, 345.85, 348.10, 349.55, 348.20, 350.45, 351.90, 350.55, 352.80, 354.25, 352.90, 355.15, 356.60, 355.25, 357.50, 358.95, 357.60, 359.85, 361.30, 359.95, 362.20, 363.65, 362.30, 364.55, 366.00, 364.65, 366.90, 368.35, 367.00, 369.25, 370.70, 369.35, 371.60, 373.05, 371.70, 373.95, 375.40, 374.05, 376.30, 377.75, 376.40, 315.20, 316.80, 315.35, 317.60, 319.05, 317.70, 319.95, 321.40, 320.05, 322.30, 323.75, 322.40, 324.65, 326.10, 324.75, 327.00, 328.45, 327.10, 329.35, 330.80, 329.45, 331.70, 333.15, 331.80, 334.05, 335.50, 334.15, 336.40, 337.85, 336.50, 338.75, 340.20, 338.85, 341.10, 342.55, 341.20, 343.45, 344.90, 343.55, 345.80, 347.25, 345.90, 348.15, 349.60, 348.25, 350.50, 351.95, 350.60, 352.85, 354.30, 352.95, 355.20, 356.65, 355.30, 357.55, 359.00, 357.65, 359.90, 361.35, 360.00, 362.25, 363.70, 362.35, 364.60, 366.05, 364.70, 366.95, 368.40, 367.05, 369.30, 370.75, 369.40, 371.65, 373.10, 371.75, 374.00, 375.45, 374.10, 376.35, 377.80, 376.45, 378.70, 380.15, 378.80, 381.05, 382.50, 381.15, 383.40, 384.85, 383.50, 385.75, 387.20, 385.85, 388.10, 389.55, 388.20, 390.45, 391.90, 390.55, 392.80, 394.25, 392.90, 395.15, 396.60, 395.25, 397.50, 398.95, 397.60, 399.85, 401.30, 399.95, 402.20, 403.65, 402.30, 404.55, 406.00, 404.65, 406.90, 408.35, 407.00, 409.25, 410.70, 409.35, 411.60, 413.05, 411.70, 413.95, 415.40, 414.05, 416.30, 417.75, 416.40, 418.65, 420.10],
    'GOOG': [135.20, 136.00, 135.90, 137.25, 138.40, 137.15, 139.30, 140.55, 139.20, 141.45, 142.80, 141.35, 143.60, 144.95, 143.50, 145.75, 147.10, 145.65, 147.90, 149.25, 147.80, 150.05, 151.40, 149.95, 152.20, 153.55, 152.10, 154.35, 155.70, 154.25, 156.50, 157.85, 156.40, 158.65, 160.00, 158.55, 160.80, 162.15, 160.70, 162.95, 164.30, 162.85, 165.10, 166.45, 165.00, 167.25, 168.60, 167.15, 169.40, 170.75, 169.30, 171.55, 172.90, 171.45, 173.70, 175.05, 173.60, 175.85, 177.20, 175.75, 178.00, 179.35, 177.90, 180.15, 181.50, 180.05, 182.30, 183.65, 182.20, 184.45, 185.80, 184.35, 186.60, 187.95, 186.50, 188.75, 190.10, 188.65, 190.90, 192.25, 190.80, 193.05, 194.40, 192.95, 195.20, 196.55, 195.10, 197.35, 198.70, 197.25, 199.50, 200.85, 199.40, 201.65, 203.00, 201.55, 203.80, 205.15, 203.70, 140.25, 141.60, 140.15, 142.40, 143.75, 142.30, 144.55, 145.90, 144.45, 146.70, 148.05, 146.60, 148.85, 150.20, 148.75, 151.00, 152.35, 150.90, 153.15, 154.50, 153.05, 155.30, 156.65, 155.20, 157.45, 158.80, 157.35, 159.60, 160.95, 159.50, 161.75, 163.10, 161.65, 163.90, 165.25, 163.80, 166.05, 167.40, 165.95, 168.20, 169.55, 168.10, 170.35, 171.70, 170.25, 172.50, 173.85, 172.40, 174.65, 176.00, 174.55, 176.80, 178.15, 176.70, 178.95, 180.30, 178.85, 181.10, 182.45, 181.00, 183.25, 184.60, 183.15, 185.40, 186.75, 185.30, 187.55, 188.90, 187.45, 189.70, 191.05, 189.60, 191.85, 193.20, 191.75, 194.00, 195.35, 193.90, 196.15, 197.50, 196.05, 198.30, 199.65, 198.20, 200.45, 201.80, 200.35, 202.60, 203.95, 202.50, 204.75, 206.10, 204.65, 206.90, 208.25, 206.80, 209.05, 210.40, 208.95, 211.20, 212.55, 211.10, 213.35, 214.70, 213.25, 215.50, 216.85, 215.40, 217.65, 219.00, 217.55, 219.80, 221.15, 219.70, 221.95, 223.30, 221.85, 224.10, 225.45, 224.00, 226.25, 227.60, 226.15, 228.40, 229.75, 228.30, 230.55, 231.90, 230.45, 232.70, 234.05, 232.60, 234.85, 236.20],
    'AMZN': [145.50, 146.80, 145.35, 147.60, 148.95, 147.50, 149.75, 151.10, 149.65, 151.90, 153.25, 151.80, 154.05, 155.40, 153.95, 156.20, 157.55, 156.10, 158.35, 159.70, 158.25, 160.50, 161.85, 160.40, 162.65, 164.00, 162.55, 164.80, 166.15, 164.70, 166.95, 168.30, 166.85, 169.10, 170.45, 169.00, 171.25, 172.60, 171.15, 173.40, 174.75, 173.30, 175.55, 176.90, 175.45, 177.70, 179.05, 177.60, 179.85, 181.20, 179.75, 182.00, 183.35, 181.90, 184.15, 185.50, 184.05, 186.30, 187.65, 186.20, 188.45, 189.80, 188.35, 190.60, 191.95, 190.50, 192.75, 194.10, 192.65, 194.90, 196.25, 194.80, 197.05, 198.40, 196.95, 199.20, 200.55, 199.10, 201.35, 202.70, 201.25, 203.50, 204.85, 203.40, 205.65, 207.00, 205.55, 207.80, 209.15, 207.70, 209.95, 211.30, 209.85, 212.10, 213.45, 212.00, 214.25, 215.60, 214.15, 148.80, 150.25, 148.80, 151.05, 152.40, 150.95, 153.20, 154.55, 153.10, 155.35, 156.70, 155.25, 157.50, 158.85, 157.40, 159.65, 161.00, 159.55, 161.80, 163.15, 161.70, 163.95, 165.30, 163.85, 166.10, 167.45, 166.00, 168.25, 169.60, 168.15, 170.40, 171.75, 170.30, 172.55, 173.90, 172.45, 174.70, 176.05, 174.60, 176.85, 178.20, 176.75, 179.00, 180.35, 178.90, 181.15, 182.50, 181.05, 183.30, 184.65, 183.20, 185.45, 186.80, 185.35, 187.60, 188.95, 187.50, 189.75, 191.10, 189.65, 191.90, 193.25, 191.80, 194.05, 195.40, 193.95, 196.20, 197.55, 196.10, 198.35, 199.70, 198.25, 200.50, 201.85, 200.40, 202.65, 204.00, 202.55, 204.80, 206.15, 204.70, 206.95, 208.30, 206.85, 209.10, 210.45, 209.00, 211.25, 212.60, 211.15, 213.40, 214.75, 213.30, 215.55, 216.90, 215.45, 217.70, 219.05, 217.60, 219.85, 221.20, 219.75, 222.00, 223.35, 221.90, 224.15, 225.50, 224.05, 226.30, 227.65, 226.20, 228.45, 229.80, 228.35, 230.60, 231.95, 230.50, 232.75, 234.10, 232.65, 234.90, 236.25, 234.80, 237.05, 238.40],
    'TSLA': [242.50, 245.80, 243.15, 248.30, 251.75, 247.90, 253.45, 257.20, 252.65, 258.90, 263.45, 258.10, 264.75, 269.30, 263.95, 270.60, 275.15, 269.80, 276.45, 281.00, 275.65, 282.30, 286.85, 281.50, 288.15, 292.70, 287.35, 294.00, 298.55, 293.20, 299.85, 304.40, 299.05, 305.70, 310.25, 304.90, 311.55, 316.10, 310.75, 317.40, 321.95, 316.60, 323.25, 327.80, 322.45, 329.10, 333.65, 328.30, 334.95, 339.50, 334.15, 340.80, 345.35, 340.00, 346.65, 351.20, 345.85, 352.50, 357.05, 351.70, 358.35, 362.90, 357.55, 364.20, 368.75, 363.40, 370.05, 374.60, 369.25, 375.90, 380.45, 375.10, 381.75, 386.30, 380.95, 387.60, 392.15, 386.80, 393.45, 398.00, 392.65, 399.30, 403.85, 398.50, 405.15, 409.70, 404.35, 411.00, 415.55, 410.20, 416.85, 421.40, 416.05, 422.70, 427.25, 421.90, 428.55, 433.10, 427.75, 252.80, 257.45, 251.90, 258.55, 263.10, 257.75, 264.40, 268.95, 263.60, 270.25, 274.80, 269.45, 276.10, 280.65, 275.30, 281.95, 286.50, 281.15, 287.80, 292.35, 287.00, 293.65, 298.20, 292.85, 299.50, 304.05, 298.70, 305.35, 309.90, 304.55, 311.20, 315.75, 310.40, 317.05, 321.60, 316.25, 322.90, 327.45, 322.10, 328.75, 333.30, 327.95, 334.60, 339.15, 333.80, 340.45, 345.00, 339.65, 346.30, 350.85, 345.50, 352.15, 356.70, 351.35, 358.00, 362.55, 357.20, 363.85, 368.40, 363.05, 369.70, 374.25, 368.90, 375.55, 380.10, 374.75, 381.40, 385.95, 380.60, 387.25, 391.80, 386.45, 393.10, 397.65, 392.30, 398.95, 403.50, 398.15, 404.80, 409.35, 404.00, 410.65, 415.20, 409.85, 416.50, 421.05, 415.70, 422.35, 426.90, 421.55, 428.20, 432.75, 427.40, 434.05, 438.60, 433.25, 439.90, 444.45, 439.10, 445.75, 450.30, 444.95, 451.60, 456.15, 450.80, 457.45, 462.00, 456.65, 463.30, 467.85, 462.50, 469.15, 473.70],
    'NVDA': [485.20, 490.75, 483.40, 496.30, 503.85, 492.50, 509.40, 517.95, 505.60, 523.50, 532.05, 518.70, 537.60, 546.15, 532.80, 551.70, 560.25, 546.90, 565.80, 574.35, 561.00, 579.90, 588.45, 575.10, 594.00, 602.55, 589.20, 608.10, 616.65, 603.30, 622.20, 630.75, 617.40, 636.30, 644.85, 631.50, 650.40, 658.95, 645.60, 664.50, 673.05, 659.70, 678.60, 687.15, 673.80, 692.70, 701.25, 687.90, 706.80, 715.35, 702.00, 720.90, 729.45, 716.10, 735.00, 743.55, 730.20, 749.10, 757.65, 744.30, 763.20, 771.75, 758.40, 777.30, 785.85, 772.50, 791.40, 799.95, 786.60, 805.50, 814.05, 800.70, 819.60, 828.15, 814.80, 833.70, 842.25, 828.90, 847.80, 856.35, 843.00, 861.90, 870.45, 857.10, 876.00, 884.55, 871.20, 890.10, 898.65, 885.30, 904.20, 912.75, 899.40, 918.30, 926.85, 913.50, 932.40, 940.95, 927.60, 495.50, 504.25, 491.80, 510.55, 519.30, 506.85, 525.60, 534.35, 521.90, 540.65, 549.40, 536.95, 555.70, 564.45, 552.00, 570.75, 579.50, 567.05, 585.80, 594.55, 582.10, 600.85, 609.60, 597.15, 615.90, 624.65, 612.20, 630.95, 639.70, 627.25, 646.00, 654.75, 642.30, 661.05, 669.80, 657.35, 676.10, 684.85, 672.40, 691.15, 699.90, 687.45, 706.20, 714.95, 702.50, 721.25, 730.00, 717.55, 736.30, 745.05, 732.60, 751.35, 760.10, 747.65, 766.40, 775.15, 762.70, 781.45, 790.20, 777.75, 796.50, 805.25, 792.80, 811.55, 820.30, 807.85, 826.60, 835.35, 822.90, 841.65, 850.40, 837.95, 856.70, 865.45, 853.00, 871.75, 880.50, 868.05, 886.80, 895.55, 883.10, 901.85, 910.60, 898.15, 916.90, 925.65, 913.20, 931.95, 940.70, 928.25, 947.00, 955.75, 943.30, 962.05, 970.80, 958.35, 977.10, 985.85, 973.40, 992.15, 1000.90, 988.45, 1007.20, 1015.95, 1003.50, 1022.25, 1031.00, 1018.55, 1037.30, 1046.05, 1033.60, 1052.35, 1061.10, 1048.65, 1067.40, 1076.15],
    'JPM': [145.30, 146.85, 144.75, 148.40, 150.95, 147.85, 151.50, 154.05, 150.95, 154.60, 157.15, 154.05, 157.70, 160.25, 157.15, 160.80, 163.35, 160.25, 163.90, 166.45, 163.35, 167.00, 169.55, 166.45, 170.10, 172.65, 169.55, 173.20, 175.75, 172.65, 176.30, 178.85, 175.75, 179.40, 181.95, 178.85, 182.50, 185.05, 181.95, 185.60, 188.15, 185.05, 188.70, 191.25, 188.15, 191.80, 194.35, 191.25, 194.90, 197.45, 194.35, 198.00, 200.55, 197.45, 201.10, 203.65, 200.55, 204.20, 206.75, 203.65, 207.30, 209.85, 206.75, 210.40, 212.95, 209.85, 213.50, 216.05, 212.95, 216.60, 219.15, 216.05, 219.70, 222.25, 219.15, 222.80, 225.35, 222.25, 225.90, 228.45, 225.35, 229.00, 231.55, 228.45, 232.10, 234.65, 231.55, 235.20, 237.75, 234.65, 238.30, 240.85, 237.75, 241.40, 243.95, 240.85, 244.50, 247.05, 243.95, 148.60, 151.25, 147.95, 151.60, 154.15, 151.05, 154.70, 157.25, 154.15, 157.80, 160.35, 157.25, 160.90, 163.45, 160.35, 164.00, 166.55, 163.45, 167.10, 169.65, 166.55, 170.20, 172.75, 169.65, 173.30, 175.85, 172.75, 176.40, 178.95, 175.85, 179.50, 182.05, 178.95, 182.60, 185.15, 182.05, 185.70, 188.25, 185.15, 188.80, 191.35, 188.25, 191.90, 194.45, 191.35, 195.00, 197.55, 194.45, 198.10, 200.65, 197.55, 201.20, 203.75, 200.65, 204.30, 206.85, 203.75, 207.40, 209.95, 206.85, 210.50, 213.05, 209.95, 213.60, 216.15, 213.05, 216.70, 219.25, 216.15, 219.80, 222.35, 219.25, 222.90, 225.45, 222.35, 226.00, 228.55, 225.45, 229.10, 231.65, 228.55, 232.20, 234.75, 231.65, 235.30, 237.85, 234.75, 238.40, 240.95, 237.85, 241.50, 244.05, 240.95, 244.60, 247.15, 244.05, 247.70, 250.25, 247.15, 250.80, 253.35, 250.25, 253.90, 256.45, 253.35, 257.00, 259.55, 256.45, 260.10, 262.65, 259.55, 263.20, 265.75, 262.65, 266.30, 268.85, 265.75, 269.40, 271.95, 268.85, 272.50, 275.05],
    'V': [235.40, 237.85, 234.95, 240.30, 243.75, 238.85, 244.20, 247.65, 242.75, 248.10, 251.55, 246.65, 252.00, 255.45, 250.55, 255.90, 259.35, 254.45, 259.80, 263.25, 258.35, 263.70, 267.15, 262.25, 267.60, 271.05, 266.15, 271.50, 274.95, 270.05, 275.40, 278.85, 273.95, 279.30, 282.75, 277.85, 283.20, 286.65, 281.75, 287.10, 290.55, 285.65, 291.00, 294.45, 289.55, 294.90, 298.35, 293.45, 298.80, 302.25, 297.35, 302.70, 306.15, 301.25, 306.60, 310.05, 305.15, 310.50, 313.95, 309.05, 314.40, 317.85, 312.95, 318.30, 321.75, 316.85, 322.20, 325.65, 320.75, 326.10, 329.55, 324.65, 330.00, 333.45, 328.55, 333.90, 337.35, 332.45, 337.80, 341.25, 336.35, 341.70, 345.15, 340.25, 345.60, 349.05, 344.15, 349.50, 352.95, 348.05, 353.40, 356.85, 351.95, 357.30, 360.75, 355.85, 361.20, 364.65, 359.75, 238.70, 242.25, 237.25, 242.60, 246.05, 241.15, 246.50, 249.95, 245.05, 250.40, 253.85, 248.95, 254.30, 257.75, 252.85, 258.20, 261.65, 256.75, 262.10, 265.55, 260.65, 266.00, 269.45, 264.55, 269.90, 273.35, 268.45, 273.80, 277.25, 272.35, 277.70, 281.15, 276.25, 281.60, 285.05, 280.15, 285.50, 288.95, 284.05, 289.40, 292.85, 287.95, 293.30, 296.75, 291.85, 297.20, 300.65, 295.75, 301.10, 304.55, 299.65, 305.00, 308.45, 303.55, 308.90, 312.35, 307.45, 312.80, 316.25, 311.35, 316.70, 320.15, 315.25, 320.60, 324.05, 319.15, 324.50, 327.95, 323.05, 328.40, 331.85, 326.95, 332.30, 335.75, 330.85, 336.20, 339.65, 334.75, 340.10, 343.55, 338.65, 344.00, 347.45, 342.55, 347.90, 351.35, 346.45, 351.80, 355.25, 350.35, 355.70, 359.15, 354.25, 359.60, 363.05, 358.15, 363.50, 366.95, 362.05, 367.40, 370.85, 365.95, 371.30, 374.75, 369.85, 375.20, 378.65, 373.75, 379.10, 382.55, 377.65, 383.00, 386.45, 381.55, 386.90, 390.35, 385.45, 390.80, 394.25]
}

class PortfolioOptimizer:
    """Advanced portfolio optimizer with multiple strategies"""
    
    def __init__(self, tickers, risk_free_rate=0.02):
        self.tickers = tickers
        self.risk_free_rate = risk_free_rate
        self.returns_df = None
        self.mean_returns = None
        self.cov_matrix = None
        
    def load_data(self):
        """Load and process price data"""
        try:
            # Validate tickers
            valid_tickers = [t for t in self.tickers if t in MOCK_PRICE_DATA]
            if len(valid_tickers) < 2:
                raise ValueError(f"Need at least 2 valid tickers. Available: {', '.join(MOCK_PRICE_DATA.keys())}")
            
            # Create price dataframe with aligned lengths (use most recent overlapping window)
            price_data = {ticker: MOCK_PRICE_DATA[ticker] for ticker in valid_tickers}
            min_length = min(len(prices) for prices in price_data.values())
            if min_length < 2:
                raise ValueError("Not enough overlapping price history for selected tickers")

            aligned_data = {
                ticker: np.array(prices[-min_length:], dtype=float)
                for ticker, prices in price_data.items()
            }
            prices_df = pd.DataFrame(aligned_data)
            
            # Calculate log returns
            self.returns_df = np.log(prices_df / prices_df.shift(1)).dropna()
            
            # Calculate mean returns and covariance (annualized)
            self.mean_returns = self.returns_df.mean() * 252
            self.cov_matrix = self.returns_df.cov() * 252
            
            self.tickers = valid_tickers
            return True
        except Exception as e:
            raise Exception(f"Error loading data: {str(e)}")
    
    def portfolio_stats(self, weights):
        """Calculate portfolio statistics"""
        weights = np.array(weights)
        returns = np.sum(self.mean_returns * weights)
        volatility = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
        sharpe = (returns - self.risk_free_rate) / volatility
        return returns, volatility, sharpe
    
    def monte_carlo_simulation(self, num_portfolios=10000):
        """Run Monte Carlo simulation"""
        results = np.zeros((4, num_portfolios))
        weights_record = []
        
        for i in range(num_portfolios):
            # Generate random weights
            weights = np.random.random(len(self.tickers))
            weights /= np.sum(weights)
            weights_record.append(weights)
            
            # Calculate portfolio stats
            returns, volatility, sharpe = self.portfolio_stats(weights)
            
            results[0, i] = returns
            results[1, i] = volatility
            results[2, i] = sharpe
            results[3, i] = i
        
        return results, weights_record
    
    def optimize_sharpe(self):
        """Optimize for maximum Sharpe ratio using scipy"""
        num_assets = len(self.tickers)
        
        def neg_sharpe(weights):
            _, _, sharpe = self.portfolio_stats(weights)
            return -sharpe
        
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0, 1) for _ in range(num_assets))
        initial_guess = num_assets * [1. / num_assets]
        
        result = minimize(neg_sharpe, initial_guess, method='SLSQP', 
                         bounds=bounds, constraints=constraints)
        
        return result.x
    
    def optimize_min_volatility(self):
        """Optimize for minimum volatility"""
        num_assets = len(self.tickers)
        
        def portfolio_volatility(weights):
            _, volatility, _ = self.portfolio_stats(weights)
            return volatility
        
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0, 1) for _ in range(num_assets))
        initial_guess = num_assets * [1. / num_assets]
        
        result = minimize(portfolio_volatility, initial_guess, method='SLSQP',
                         bounds=bounds, constraints=constraints)
        
        return result.x
    
    def optimize_target_return(self, target_return):
        """Optimize for minimum volatility given target return"""
        num_assets = len(self.tickers)
        
        def portfolio_volatility(weights):
            _, volatility, _ = self.portfolio_stats(weights)
            return volatility
        
        constraints = (
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
            {'type': 'eq', 'fun': lambda x: np.sum(self.mean_returns * x) - target_return}
        )
        bounds = tuple((0, 1) for _ in range(num_assets))
        initial_guess = num_assets * [1. / num_assets]
        
        result = minimize(portfolio_volatility, initial_guess, method='SLSQP',
                         bounds=bounds, constraints=constraints)
        
        return result.x if result.success else None
    
    def efficient_frontier(self, num_points=100):
        """Generate efficient frontier curve"""
        min_return = self.mean_returns.min()
        max_return = self.mean_returns.max()
        target_returns = np.linspace(min_return, max_return, num_points)
        
        efficient_portfolios = []
        for target in target_returns:
            weights = self.optimize_target_return(target)
            if weights is not None:
                returns, volatility, sharpe = self.portfolio_stats(weights)
                efficient_portfolios.append({
                    'return': returns,
                    'volatility': volatility,
                    'sharpe': sharpe,
                    'weights': weights.tolist()
                })
        
        return efficient_portfolios

    def render_portfolio_chart(self, mc_results, frontier=None, optimal=None,
                               risk_free_rate=None, num_portfolios=None):
        """Render efficient frontier and Monte Carlo scatter plot using matplotlib"""
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 6))

        # Monte Carlo scatter colored by Sharpe ratio
        scatter = ax.scatter(
            mc_results[1],
            mc_results[0],
            c=mc_results[2],
            cmap='viridis',
            s=12,
            alpha=0.45,
            edgecolor='none',
            label='Monte Carlo Portfolios'
        )

        cbar = fig.colorbar(scatter, ax=ax)
        cbar.set_label('Sharpe Ratio', color='white')
        cbar.ax.yaxis.set_tick_params(color='white')
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')

        # Efficient frontier curve
        if frontier:
            frontier_vol = [point['volatility'] for point in frontier]
            frontier_ret = [point['return'] for point in frontier]
            ax.plot(frontier_vol, frontier_ret, color='#ffb454', linewidth=2.5, label='Efficient Frontier')

        # Optimal portfolio point
        if optimal:
            ax.scatter(
                optimal['volatility'],
                optimal['return'],
                color='#ff4d4f',
                marker='*',
                s=320,
                label='Optimal Portfolio'
            )

        title_parts = ['Efficient Frontier & Portfolio Scatter']
        if risk_free_rate is not None:
            title_parts.append(f"Risk-Free: {risk_free_rate * 100:.2f}%")
        if num_portfolios is not None:
            title_parts.append(f"Simulations: {num_portfolios:,}")
        ax.set_title(' | '.join(title_parts), color='white', fontsize=14, pad=16)
        ax.set_xlabel('Volatility (Std. Dev)', color='white')
        ax.set_ylabel('Expected Return', color='white')
        ax.tick_params(axis='both', colors='white')
        ax.grid(color='white', alpha=0.1)
        legend = ax.legend(facecolor='#1f2937', edgecolor='none', framealpha=0.8, labelcolor='white')
        for text in legend.get_texts():
            text.set_color('white')

        fig.tight_layout()
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')

    def render_correlation_heatmap(self):
        """Render correlation heatmap for selected assets"""
        if self.returns_df is None:
            raise ValueError('Returns data not loaded')

        corr = self.returns_df.corr()
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(8, 6))

        cax = ax.imshow(corr.values, cmap='coolwarm', vmin=-1, vmax=1)
        fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04, label='Correlation')

        tick_labels = corr.columns
        ax.set_xticks(range(len(tick_labels)))
        ax.set_yticks(range(len(tick_labels)))
        ax.set_xticklabels(tick_labels, rotation=45, ha='right', color='white')
        ax.set_yticklabels(tick_labels, color='white')

        ax.set_title('Asset Correlation Heatmap', color='white', fontsize=14, pad=16)
        ax.grid(False)

        fig.tight_layout()
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')

# API Routes
@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/tickers', methods=['GET'])
def get_available_tickers():
    """Get list of available tickers"""
    return jsonify({
        'success': True,
        'tickers': list(MOCK_PRICE_DATA.keys())
    })

@app.route('/api/optimize', methods=['POST'])
def optimize_portfolio():
    """Optimize portfolio using specified strategy"""
    try:
        data = request.json
        tickers = [t.strip().upper() for t in data.get('tickers', [])]
        strategy = data.get('strategy', 'max_sharpe')
        risk_free_rate = data.get('risk_free_rate', 0.02)
        num_simulations = data.get('num_simulations', 10000)
        
        if len(tickers) < 2:
            return jsonify({'success': False, 'error': 'Need at least 2 tickers'}), 400
        
        # Initialize optimizer
        optimizer = PortfolioOptimizer(tickers, risk_free_rate)
        optimizer.load_data()

        # Run Monte Carlo simulation and efficient frontier
        mc_results, mc_weights = optimizer.monte_carlo_simulation(num_simulations)
        frontier = optimizer.efficient_frontier(100)
        
        # Get optimal portfolio based on strategy
        if strategy == 'max_sharpe':
            optimal_weights = optimizer.optimize_sharpe()
        elif strategy == 'min_volatility':
            optimal_weights = optimizer.optimize_min_volatility()
        elif strategy == 'monte_carlo':
            # Use best from Monte Carlo
            max_sharpe_idx = np.argmax(mc_results[2])
            optimal_weights = mc_weights[max_sharpe_idx]
        else:
            return jsonify({'success': False, 'error': 'Invalid strategy'}), 400
        
        # Calculate optimal portfolio stats
        opt_return, opt_volatility, opt_sharpe = optimizer.portfolio_stats(optimal_weights)

        optimal_summary = {
            'weights': {ticker: float(weight) for ticker, weight in zip(optimizer.tickers, optimal_weights)},
            'return': float(opt_return),
            'volatility': float(opt_volatility),
            'sharpe': float(opt_sharpe)
        }

        # Render backend chart image
        chart_image = optimizer.render_portfolio_chart(
            mc_results,
            frontier=frontier,
            optimal=optimal_summary,
            risk_free_rate=risk_free_rate,
            num_portfolios=num_simulations
        )
        
        # Save to database
        conn = sqlite3.connect('portfolio.db')
        c = conn.cursor()
        c.execute('''INSERT INTO optimizations 
                     (timestamp, tickers, strategy, optimal_weights, expected_return, 
                      volatility, sharpe_ratio, risk_free_rate)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (datetime.now().isoformat(), ','.join(optimizer.tickers), strategy,
                   json.dumps(optimal_weights.tolist()), float(opt_return), 
                   float(opt_volatility), float(opt_sharpe), risk_free_rate))
        conn.commit()
        optimization_id = c.lastrowid
        conn.close()
        
        # Prepare response
        response = {
            'success': True,
            'optimization_id': optimization_id,
            'optimal': optimal_summary,
            'monte_carlo': {
                'returns': mc_results[0].tolist(),
                'volatilities': mc_results[1].tolist(),
                'sharpes': mc_results[2].tolist()
            },
            'tickers': optimizer.tickers,
            'strategy': strategy,
            'frontier': frontier,
            'chart_image': chart_image
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/efficient-frontier', methods=['POST'])
def get_efficient_frontier():
    """Calculate efficient frontier"""
    try:
        data = request.json
        tickers = [t.strip().upper() for t in data.get('tickers', [])]
        risk_free_rate = data.get('risk_free_rate', 0.02)
        num_points = data.get('num_points', 50)
        
        optimizer = PortfolioOptimizer(tickers, risk_free_rate)
        optimizer.load_data()
        
        frontier = optimizer.efficient_frontier(num_points)
        
        return jsonify({
            'success': True,
            'frontier': frontier,
            'tickers': optimizer.tickers
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/portfolio-stats', methods=['POST'])
def calculate_portfolio_stats():
    """Calculate statistics for custom weights"""
    try:
        data = request.json
        tickers = data.get('tickers', [])
        weights = data.get('weights', [])
        risk_free_rate = data.get('risk_free_rate', 0.02)
        
        if len(tickers) != len(weights):
            return jsonify({'success': False, 'error': 'Tickers and weights length mismatch'}), 400
        
        if abs(sum(weights) - 1.0) > 0.01:
            return jsonify({'success': False, 'error': 'Weights must sum to 1'}), 400
        
        optimizer = PortfolioOptimizer(tickers, risk_free_rate)
        optimizer.load_data()
        
        returns, volatility, sharpe = optimizer.portfolio_stats(weights)
        
        return jsonify({
            'success': True,
            'return': float(returns),
            'volatility': float(volatility),
            'sharpe': float(sharpe)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_optimization_history():
    """Get optimization history from database"""
    try:
        conn = sqlite3.connect('portfolio.db')
        c = conn.cursor()
        c.execute('''SELECT id, timestamp, tickers, strategy, optimal_weights, 
                     expected_return, volatility, sharpe_ratio 
                     FROM optimizations 
                     ORDER BY timestamp DESC 
                     LIMIT 50''')
        rows = c.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'id': row[0],
                'timestamp': row[1],
                'tickers': row[2].split(','),
                'strategy': row[3],
                'optimal_weights': json.loads(row[4]),
                'expected_return': row[5],
                'volatility': row[6],
                'sharpe_ratio': row[7]
            })
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/correlation', methods=['POST'])
def get_correlation_matrix():
    """Get correlation matrix for selected tickers"""
    try:
        data = request.json
        tickers = [t.strip().upper() for t in data.get('tickers', [])]
        
        optimizer = PortfolioOptimizer(tickers)
        optimizer.load_data()
        
        correlation = optimizer.returns_df.corr()
        heatmap_image = optimizer.render_correlation_heatmap()
        
        return jsonify({
            'success': True,
            'correlation': correlation.to_dict(),
            'tickers': optimizer.tickers,
            'chart_image': heatmap_image
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Modern Portfolio Theory Optimizer Server")
    print("📊 Available tickers:", ', '.join(MOCK_PRICE_DATA.keys()))
    print("🌐 Server running at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
