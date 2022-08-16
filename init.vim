" Vim-plug
let data_dir = has('nvim') ? stdpath('data') . '/site' : '~/.vim'
if empty(glob(data_dir . '/autoload/plug.vim'))
  silent execute '!curl -fLo '.data_dir.'/autoload/plug.vim --create-dirs  https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim'
  autocmd VimEnter * PlugInstall --sync | source $MYVIMRC
endif
call plug#begin()
    " Colour Scheme
    "Plug 'EdenEast/nightfox.nvim' 
    "Plug 'NLKNguyen/papercolor-theme'
    Plug 'franbach/miramare'
    
    " Utilities
    Plug 'sheerun/vim-polyglot'
    Plug 'jiangmiao/auto-pairs'
    Plug 'ap/vim-css-color'
    Plug 'preservim/nerdtree'

    " Completion / linters / formatters / debuggers
    Plug 'neoclide/coc.nvim',  {'branch': 'release', 'do': 'yarn install'}
    Plug 'plasticboy/vim-markdown'
    Plug 'iamcco/markdown-preview.nvim', { 'do': 'cd app && yarn install' }
    "Plug 'godlygeek/tabular'
    "Plug 'mfussenegger/nvim-dap'
    
    " Git
"    Plug 'airblade/vim-gitgutter'
      
    " Appearance
    Plug 'vim-airline/vim-airline'
    Plug 'vim-airline/vim-airline-themes'
    Plug 'ryanoasis/vim-devicons'
call plug#end()

"Plug-in Options
  " Lua requires
    "lua require('util') 
  " Airline
    let g:airline_themes='miramare'
    let g:airline_powerline_fonts=1
    let g:airline#extensions#tabline#enables=1

  " NERDTree
    let NERDTreeShowHidden=1 

  " Coc
    command! -nargs=0 Prettier :call CocAction('runCommand', 'prettier.formatFile')

" Terminal-Based settings (font, colours, etc.)
set t_ZH=^[[3m
set t_ZR=^[[23m
highlight Comment cterm=italic
set t_Co=256
  " If 256 colours is not supported by terminal (i.e. not $TERM var)
if $TERM !=? 'xterm-256color'
  set termguicolors
endif

" Options
"set background=dark
colorscheme miramare
set clipboard=unnamedplus
set completeopt=noinsert,menuone,noselect
set cursorline
set hidden
set inccommand=split
"set mouse=a
set number
"set relativenumber
set splitbelow splitright
set title
set ttimeoutlen=0
set wildmenu


" Tab size
set expandtab
set shiftwidth=2
set tabstop=2

" File browser (in-built)
let g:netrw_banner=0
let g:netrw_liststyle=0
let g:netrw_browse_split=4
let g:netrw_altv=1
let g:netrw_winsize=25
let g:netrw_keepdir=0
let g:netrw_localcopydircmd='cp -r'


" Keyboard mappings
inoremap <silent> ,s <C-r>=CocActionAsync('showSignatureHelp')<CR>
nnoremap <C-s> <Plug>MarkdownPreviewToggle
nnoremap <A-]> <cmd>call CocActionAsync('jumpDefinition')<CR>
nnoremap <A-[> <cmd>call CocActionAsync('jumpTypeDefinition')<CR>
nnoremap <A-'> <cmd>call CocActionAsync('jumpReferences')<CR>

" Vimscript stuff
filetype plugin indent on
syntax on

