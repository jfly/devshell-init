# devshell-init

Run this command in a repo to create a `.envrc` for
[`direnv`](https://direnv.net/).

The idea is that after cloning a random project, I'd like to minimize the steps
to doing work on the repo. Nix and Direnv are a beautiful match for this, but
there's a little bit of dancing required to do this:

- Create a `.envrc`
- Do... something with `git` to avoid tracking the `.envrc` file, and direnv's
  `.direnv` directory. I prefer to put them in `.git/info/exclude` as they don't
  really belong in a project specific `.gitignore`. I also don't want them in a
  systemwide `.gitignore`, as I *do* commit these files in repos I control.

`devshell-init` does this for you. It also accepts few options, such as
`--check`, which is useful for checking if the devshell defined for your project
is something it knows how to recreate.
