import sys
import performance
if __name__=='__main__':performance.main(*sys.argv[1:],modes=('plain','pipeline','feedback','coupled'))
