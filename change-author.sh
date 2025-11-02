#!/bin/bash

# Script to change Git commit author for all commits
# Usage: ./change-author.sh "New Name" "new.email@example.com"

NEW_NAME="$1"
NEW_EMAIL="$2"

if [ -z "$NEW_NAME" ] || [ -z "$NEW_EMAIL" ]; then
    echo "Usage: ./change-author.sh \"Full Name\" \"email@example.com\""
    echo "Example: ./change-author.sh \"John Doe\" \"john@example.com\""
    exit 1
fi

echo "Changing all commit authors to:"
echo "Name: $NEW_NAME"
echo "Email: $NEW_EMAIL"
echo ""
echo "⚠️  WARNING: This will rewrite Git history!"
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

git filter-branch -f --env-filter "
    export GIT_AUTHOR_NAME='$NEW_NAME'
    export GIT_AUTHOR_EMAIL='$NEW_EMAIL'
    export GIT_COMMITTER_NAME='$NEW_NAME'
    export GIT_COMMITTER_EMAIL='$NEW_EMAIL'
" --tag-name-filter cat -- --branches --tags

echo ""
echo "✅ Done! All commits now authored by $NEW_NAME <$NEW_EMAIL>"
echo ""
echo "To verify, run: git log --format='%an %ae'"
