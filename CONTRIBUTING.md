Based on Odoo Contributing documentation.

# Reporting Issues

1. Make sure you've actually read the error message if there is one, it may really help
2. No need to create an issue if you're [making a PR](https://github.com/odoo-dominicana/l10n-dominicana/wiki/Contributing#making-pull-requests) to fix it. Describe the issue in the PR, it's the same as an issue, but with higher priority!
3. Double-check that the issue still occurs with both latest version of this repository and Odoo
4. [Search](https://github.com/odoo-dominicana/l10n-dominicana/issues) for similar issues before reporting anything
5. If you're not sure it's a bug,  ask a question on [Telegram](https://t.me/odoord) or [Facebook](https://www.facebook.com/groups/odoo.dominicana/) groups to find it out
6. If you're a programmer, try investigating/fixing yourself, and consider making a Pull Request instead
7. If you really think a new issue is useful, keep in mind that it will be treated with a much lower priority than a Pull Request

If later on you create a pull request solving an opened issue, do not forget to reference it in your pull request (e.g.: "This patch fixes issue #42").

When reporting an issue or creating a pull request, please **use the following template**:

    **Quantity field is ignored in a sale order**

    Impacted versions:
 
     - 11.0
 
    Steps to reproduce:
 
     1. create a new sale order
     2. add a line with product 'Service', quantity 2, unit price 10.0
     3. validate the sale order
 
    Current behavior:
 
     - Total price of 10.0
 
    Expected behavior:
 
    - Total price of 20.0 (2 * 10 = 20)

**When appropriate please provide screenshots and/or screencast demonstrating the issue.**

Don't forget that a bug obvious to you may not be to others (maybe not using the same modules, etc.), don't neglect reproducing conditions!

If you have a code error (a.k.a. traceback), do include it in your bug report using code marks (**not a screenshot!**).

    ```
    Traceback (most recent call last):
    ...
    ```

# Making Pull Requests

1. Make sure you target the **right branch**
2. Keep your changes minimal, and strictly related to your issue (make other PRs if needed)
3. Match the style of the surrounding code, in terms of whitespace, wrapping, etc.
4. Explain why you are doing a change, not what (should be understandable from the diff)
5. Minimal commits! Rebase and squash your changes whenever you modify your PR and before submitting
6. No conflicts! Rebase off the target branch just before submitting

**Important: Please do NOT create pull requests with the same patch on multiple target branches. Fixes made in LTS versions (currently 11.0, 12.0, 13.0) will be forward ported to upper versions.**

# Further information
* [About issues](https://help.github.com/en/github/managing-your-work-on-github/about-issues)
* [Creating an issue](https://help.github.com/en/github/managing-your-work-on-github/creating-an-issue)
* [About pull requests](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/about-pull-requests)
* [About comparing branches in pull requests](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/about-comparing-branches-in-pull-requests)
* [Creating a pull request](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request)
* [About forks](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/about-forks)
* [Configuring a remote for a fork](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/configuring-a-remote-for-a-fork)
* [Creating a pull request from a fork](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request-from-a-fork)
* [Requesting a pull request review](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/requesting-a-pull-request-review)
* [Committing changes to a pull request branch created from a fork](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/committing-changes-to-a-pull-request-branch-created-from-a-fork)
