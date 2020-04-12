import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

def get_user_id():
    if g.user:
        return g.user    
    else:
        return None