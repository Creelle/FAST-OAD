.. _add-submodels:

#####################
Submodels in FAST-OAD
#####################

.. warning::

    Submodel feature is still considered as experimental.

    It as a feature for advanced users that want to replace a specific part of an existing FAST-OAD
    modules. At the very minimum, it needs a good understanding of the existing module because the
    developer is left with the responsibility to define a submodel that will work correctly in place
    of the original one.

***************
Why submodels ?
***************
FAST-OAD modules are generally associated to a discipline, and do all the related computations.
For example, the native weight module computes the masses and the centers of gravity of each
aircraft part and of the whole aircraft.

Now, let's say we want to modify the computation of wing mass. Then, we could add a new weight
module where the only difference will be in the wing mass computation. This is not satisfactory
because it would makes us copy all the code that is not related to wing mass.

To solve this problem, one solution would be to make smaller, more specific modules, and have
them assembled in the configuration file. But it would result in very complex configuration
files, and we do not want that.

There comes the principle of submodels. By using the :class:`~fastoad.module_management.service_registry.RegisterSubmodel` class in a
FAST-OAD module, it is possible to allow some parts of the model to be changed later by a
declared submodel.

*****************************************
How to use submodels in a custom module ?
*****************************************
Let's consider you want to build a custom module that will compute the number of atoms in the
fuselage and the wing (don't ask me why you would do that, it is just an assumption).

You would begin by creating two :code:`om.ExplicitComponent` classes:
:code:`CountWingAtoms` and :code:`CountFuselageAtoms`.
Then you would create the :code:`om.Group` class that will be the registered FAST-OAD module. The Python code would
look like:

.. code-block:: python

    import openmdao.api as om
    import fastoad.api as oad

    class CountWingAtoms(om.ExplicitComponent):
        """Put any implementation here"""

    class CountFuselageAtoms(om.ExplicitComponent):
        """Put any implementation here"""

    class CountEmpennageAtoms(om.ExplicitComponent):
        """Put any implementation here"""

    @oad.RegisterOpenMDAOSystem("count.atoms")
    class CountAtoms(om.Group):
        def setup(self):
            wing_component = CountWingAtoms()
            fuselage_component = CountFuselageAtoms()
            empennage_component = CountEmpennageAtoms()
            self.add_subsystem("wing", wing_component, promotes=["*"])
            self.add_subsystem("fuselage", fuselage_component, promotes=["*"])
            self.add_subsystem("empennage", empennage_component, promotes=["*"])


In the above implementation, someone that would want to provide an alternate method to count
atoms in the wing, while keeping your method for fuselage, would have to provide its own FAST-OAD
module, ideally by reusing your :code:`CountFuselageAtoms` class, but possibly by needlessly
copying it in its own code.

To allow a simpler replacement of your submodels, you will need to use the
:code:`RegisterSubmodel` class like this:

.. code-block:: python

    import openmdao.api as om
    import fastoad.api as oad

    WING_ATOM_COUNTER = "atom_counter.wing"
    FUSELAGE_ATOM_COUNTER = "atom_counter.fuselage"
    EMPENNAGE_ATOM_COUNTER = "atom_counter.empennage"

    @oad.RegisterSubmodel(WING_ATOM_COUNTER, "original.counter.wing)
    class CountWingAtoms(om.ExplicitComponent):
        """Put any implementation here"""

    @oad.RegisterSubmodel(FUSELAGE_ATOM_COUNTER, "original.counter.fuselage)
    class CountFuselageAtoms(om.ExplicitComponent):
        """Put any implementation here"""

    @oad.RegisterSubmodel(EMPENNAGE_ATOM_COUNTER, "original.counter.empennage)
    class CountEmpennageAtoms(om.ExplicitComponent):
        """Put any implementation here"""

    @oad.RegisterOpenMDAOSystem("count.atoms")
    class CountAtoms(om.Group):
        def setup(self):
            wing_component = oad.RegisterSubmodel.get_submodel(WING_ATOM_COUNTER)
            fuselage_component = oad.RegisterSubmodel.get_submodel(FUSELAGE_ATOM_COUNTER)
            empennage_component = oad.RegisterSubmodel.get_submodel(EMPENNAGE_ATOM_COUNTER)
            self.add_subsystem("wing", wing_component, promotes=["*"])
            self.add_subsystem("fuselage", fuselage_component, promotes=["*"])
            self.add_subsystem("empennage", empennage_component, promotes=["*"])

This has the same behavior as the previous one, but the second one will allow substitution of
submodels, as shown in next part.

In details, :code:`CountWingAtoms` is declared as a submodel that fulfills the role of "wing atom
counter", identified by the :code:`"atom_counter.wing"` (that is put in constant
:code:`WING_ATOM_COUNTER` to avoid typos, as it is used several times). The same applies to the
roles of "fuselage atom counter" and "empennage atom counter".

In the :code:`CountAtoms` class, the submodel that counts wing atoms is retrieved with
:code:`oad.RegisterSubmodel.get_submodel(WING_ATOM_COUNTER)`.

.. Important::

    As long as only one submodel is declared in all the used Python modules, the above instruction
    will provide it.

**********************************
How to declare a custom submodel ?
**********************************
As you have seen, we have already declared submodels in our previous custom module.
The process for providing an alternate submodel is identical:

.. code-block:: python

    import openmdao.api as om
    import fastoad.api as oad


    @oad.RegisterSubmodel("atom_counter.wing", "alternate.counter.wing")
    class CountWingAtoms(om.ExplicitComponent):
        """Put another implementation here"""


At this point, there are now 2 available submodels for the "atom_counter.wing" requirement. If we
do nothing else, the command :code:`oad.RegisterSubmodel.get_submodel("atom_counter.wing")` will
raise an error because FAST-OAD needs to be instructed what submodel to use.

The first way to do that is by Python. You may insert the following line at module level (i.e. not in
any class or function):

.. code-block:: python

    oad.RegisterSubmodel.active_models["atom_counter.wing"] = "alternate.counter.wing"

The best place for such line would probably be in the module that defines your submodel. In this
case, our above example would become:

.. code-block:: python

    import openmdao.api as om
    import fastoad.api as oad

    oad.RegisterSubmodel.active_models["atom_counter.wing"] = "alternate.counter.wing"

    @oad.RegisterSubmodel("atom_counter.wing", "alternate.counter.wing")
    class CountWingAtoms(om.ExplicitComponent):
        """Put another implementation here"""

.. warning::

    In case several Python modules define their own chosen submodel for the same requirement, the
    last interpreted line will preempt, which is not a reliable way to do.
    We currently expect such situation to be rare, where more than one alternate submodel would be
    available (for the same requirement) in one set of FAST-OAD modules.
    Anyway, in such situation, the only reliable way will be to use the configuration file, as
    instructed below.

**********************************************
How to use submodels from configuration file ?
**********************************************

The second way to define what submodels should be used is by using FAST-OAD configuration file.

.. note::

    When it comes to the specification of submodels to be used, the configuration file will have
    the priority over any Python instruction.

The configuration file can be populated with a specific section that will state the submodels
that should be chosen.

.. code-block:: yaml

    submodels:
        atom_counter.wing: alternate.counter.wing
        atom_counter.fuselage: original.counter.fuselage

In the above example, an alternate submodel is chosen for the "atom_counter.wing" requirement,
whereas the original submodel is chosen for the "original.counter.fuselage" requirement (whether
there is another one defined or not).
No submodel is defined for the "atom_counter.empennage" requirement, which lets the choice to
be done in Python, as explained in above sections.


***********************
Deactivating a submodel
***********************
It is also possible to deactivate a submodel:

.. code-block:: python

    import fastoad.api as oad

    oad.RegisterSubmodel.active_models["atom_counter.wing"] = None  # The empty string "" is also possible

Then nothing will be done when the "atom_counter.wing" submodel will be called. Of course, one
has to correctly know which variables will be missing with such setting and what consequences it
will have on the whole problem.

From the configuration file, it can be done with:

.. code-block:: yaml

    submodels:
        atom_counter.wing: null  # The empty string "" is also possible

