# Load completion functions before zoxide registers its `cd` completion.
# Keep Docker Desktop's "Configure shell completions" off; this file owns compinit.
fpath=("$HOME/.docker/completions" $fpath)
autoload -Uz compinit
compinit
