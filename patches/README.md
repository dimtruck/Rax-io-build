Downstream Patches
==================
These files control our build patch management system. They allow us to merge in changes to the upstream Raxio code
that are required for our production deployments but may not be through the review process. In general, the goal is
to have as few patches in these files as possible. Unless the dev, product, or build manager says its absolutely
required, don't add your patch here. Also, if you're not the build manager, submit a pull request to change these
files. This is not for testing your own patches. The build scripts can be easily executed outside of the build
pipeline, so you can set up your own local builds to test your patches with the current patch set.

The Rules
=========
1. DO NOT add patches yourself. Send a pull request and let the current build manager sort it.
2. DO NOT use this for testing your patches. Run the build process locally.
3. DO NOT modify hotfix unless you're the build manager.
4. DO NOT add patches from your personal repository. Official fixes should come from gerrit reviews or branches in raxio

Hotfix vs. Downstream
=====================
Hotfix is for emergency fixes to the currently deployed service only and should not be updated unless absolutely needed
and only by the build manager for that emergency hotfix. Once the hotfix is deployed, the build manager will update
the PRODUCTION branch and clear the patches from this file, so it should usually be empty.

Downstream is for the normal build chain and should shrink and grow as patches move through the review process. It is
the build manager's responsibility to monitor those patches and accept/reject pull requests for new patches.
