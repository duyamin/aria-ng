
from .. import FixedThreadPoolExecutor, Issue, AriaError, UnimplementedFunctionalityError, LockedList, print_exception, classname
from ..consumption import Validator
from ..loading import DefaultLoaderSource
from ..reading import DefaultReaderSource
from ..presentation import DefaultPresenterSource

class Parser(object):
    """
    Base class for ARIA parsers.
    
    Parsers generate presentations by consuming a data source via appropriate
    :class:`aria.loader.Loader`, :class:`aria.reader.Reader`, and :class:`aria.presenter.Presenter`
    instances.
    
    Note that parsing may internally trigger more than one loading/reading/presentation cycle,
    for example if the agnostic raw data has dependencies that must also be parsed.
    """
    
    def __init__(self, location, reader=None, presenter_class=None, loader_source=DefaultLoaderSource(), reader_source=DefaultReaderSource(), presenter_source=DefaultPresenterSource()):
        self.location = location
        self.reader = reader
        self.presenter_class = presenter_class
        self.loader_source = loader_source
        self.reader_source = reader_source
        self.presenter_source = presenter_source

    def parse(self, location):
        raise UnimplementedFunctionalityError(classname(self) + '.parse')

class DefaultParser(Parser):
    """
    The default ARIA parser supports agnostic raw data composition for presenters
    that have `\_get\_import\_locations` and `\_merge\_import`.
    
    To improve performance, loaders are called asynchronously on separate threads.
    """
    
    def parse(self, context=None):
        """
        :rtype: :class:`aria.presenter.Presenter`
        """
        
        presentation = None
        imported_presentations = None
        
        executor = FixedThreadPoolExecutor(timeout=10)
        importing_locations = LockedList()
        try:
            presentation = self._parse_all(self.location, None, self.presenter_class, executor, importing_locations)
            executor.drain()
            
            # Handle exceptions
            if context is not None:
                for e in executor.exceptions:
                    self._handle_exception(context, e)
            else:
                executor.raise_first()
                
            imported_presentations = executor.returns
        except Exception as e:
            if context is not None:
                self._handle_exception(context, e)
            else:
                raise e
        except:
            executor.close()

        # Merge imports
        if imported_presentations is not None:
            for imported_presentation in imported_presentations:
                if hasattr(presentation, '_merge_import'):
                    presentation._merge_import(imported_presentation)
                    
        return presentation
    
    def parse_and_validate(self, context):
        try:
            context.presentation = self.parse(context)
            if context.presentation is not None:
                Validator(context).consume()
        except Exception as e:
            self._handle_exception(context, e)

    def _parse_all(self, location, origin_location, presenter_class, executor, importing_locations):
        raw, location = self._parse_one(location, origin_location)
        
        if presenter_class is None:
            presenter_class = self.presenter_source.get_presenter(raw)
        
        presentation = presenter_class(raw=raw)

        if presentation is not None and hasattr(presentation, '_link'):
            presentation._link()
        
        # Submit imports to executor
        if hasattr(presentation, '_get_import_locations'):
            import_locations = presentation._get_import_locations()
            if import_locations:
                for import_location in import_locations:
                    do_import = False
                    with importing_locations:
                        if import_location not in importing_locations:
                            importing_locations.append(import_location)
                            do_import = True
                    
                    if do_import:
                        # The imports inherit the parent presenter class and use the current location as their origin location
                        executor.submit(self._parse_all, import_location, location, presenter_class, executor, importing_locations)

        return presentation
    
    def _parse_one(self, location, origin_location):
        if self.reader is not None:
            return self.reader.read(), self.reader.location
        loader = self.loader_source.get_loader(location, origin_location)
        reader = self.reader_source.get_reader(location, loader)
        return reader.read(), reader.location

    def _handle_exception(self, context, e):
        if hasattr(e, 'issue') and isinstance(e.issue, Issue):
            context.validation.report(issue=e.issue)
        else:
            context.validation.report(exception=e)
        if not isinstance(e, AriaError):
            print_exception(e)
